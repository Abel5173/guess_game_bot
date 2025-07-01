"""
Mutating Roles System - Dynamic role changes during gameplay.
"""

import random
from typing import Dict, List, Optional, Tuple
from enum import Enum
from datetime import datetime, timedelta
from bot.database import SessionLocal
from bot.database.models import Player, PlayerGameLink
import logging

logger = logging.getLogger(__name__)


class RoleType(Enum):
    CREWMATE = "crewmate"
    IMPOSTOR = "impostor"
    DETECTIVE = "detective"
    MEDIC = "medic"
    ENGINEER = "engineer"
    SHERIFF = "sheriff"
    JESTER = "jester"
    SHADOW = "shadow"


class MutationTrigger(Enum):
    ROUND_START = "round_start"
    PLAYER_DEATH = "player_death"
    TASK_COMPLETION = "task_completion"
    VOTE_ROUND = "vote_round"
    TIME_BASED = "time_based"
    RANDOM_EVENT = "random_event"


class MutatingRolesSystem:
    """Manages dynamic role changes during gameplay."""
    
    def __init__(self):
        self.active_mutations = {}  # session_id -> {player_id -> mutation_data}
        self.mutation_history = {}  # session_id -> [mutation_events]
        self.role_definitions = {
            RoleType.CREWMATE: {
                "description": "Standard crewmate - complete tasks to win",
                "abilities": ["Complete tasks", "Vote in meetings"],
                "win_condition": "Complete all tasks or identify impostors"
            },
            RoleType.IMPOSTOR: {
                "description": "Sabotage and eliminate crewmates",
                "abilities": ["Sabotage", "Kill players", "Vent"],
                "win_condition": "Eliminate enough crewmates"
            },
            RoleType.DETECTIVE: {
                "description": "Can investigate players for clues",
                "abilities": ["Investigate players", "Get investigation results", "Complete tasks"],
                "win_condition": "Complete all tasks or identify impostors"
            },
            RoleType.MEDIC: {
                "description": "Can revive one dead player per game",
                "abilities": ["Revive player", "Complete tasks", "Vote in meetings"],
                "win_condition": "Complete all tasks or identify impostors"
            },
            RoleType.ENGINEER: {
                "description": "Can fix sabotages faster and use vents",
                "abilities": ["Fast sabotage repair", "Use vents", "Complete tasks"],
                "win_condition": "Complete all tasks or identify impostors"
            },
            RoleType.SHERIFF: {
                "description": "Can kill one player per game (if they're impostor)",
                "abilities": ["Kill one player", "Complete tasks", "Vote in meetings"],
                "win_condition": "Complete all tasks or identify impostors"
            },
            RoleType.JESTER: {
                "description": "Wins by getting voted out",
                "abilities": ["Complete tasks", "Vote in meetings", "Trick others"],
                "win_condition": "Get voted out by crewmates"
            },
            RoleType.SHADOW: {
                "description": "Invisible to other players when moving",
                "abilities": ["Stealth movement", "Complete tasks", "Vote in meetings"],
                "win_condition": "Complete all tasks or identify impostors"
            }
        }
        
        self.mutation_rules = {
            MutationTrigger.ROUND_START: {
                "probability": 0.1,  # 10% chance
                "allowed_roles": [RoleType.DETECTIVE, RoleType.MEDIC, RoleType.ENGINEER],
                "description": "A mysterious force has changed your role!"
            },
            MutationTrigger.PLAYER_DEATH: {
                "probability": 0.15,  # 15% chance
                "allowed_roles": [RoleType.SHERIFF, RoleType.SHADOW],
                "description": "The death has awakened new abilities within you!"
            },
            MutationTrigger.TASK_COMPLETION: {
                "probability": 0.05,  # 5% chance
                "allowed_roles": [RoleType.ENGINEER, RoleType.DETECTIVE],
                "description": "Your dedication has unlocked new powers!"
            },
            MutationTrigger.VOTE_ROUND: {
                "probability": 0.08,  # 8% chance
                "allowed_roles": [RoleType.JESTER, RoleType.SHADOW],
                "description": "The tension of voting has transformed you!"
            },
            MutationTrigger.TIME_BASED: {
                "probability": 0.03,  # 3% chance per minute
                "allowed_roles": list(RoleType),
                "description": "Time itself has altered your destiny!"
            },
            MutationTrigger.RANDOM_EVENT: {
                "probability": 0.02,  # 2% chance
                "allowed_roles": list(RoleType),
                "description": "A random cosmic event has changed everything!"
            }
        }
    
    def check_for_mutation(self, session_id: int, trigger: MutationTrigger, 
                          player_id: int = None) -> List[Dict]:
        """Check if any players should have their roles mutated."""
        mutations = []
        
        if session_id not in self.active_mutations:
            self.active_mutations[session_id] = {}
        
        if session_id not in self.mutation_history:
            self.mutation_history[session_id] = []
        
        # Get all active players in the session
        active_players = self._get_active_players(session_id)
        
        for player in active_players:
            # Skip if player_id is specified and doesn't match
            if player_id and player["id"] != player_id:
                continue
            
            # Check mutation probability
            if self._should_mutate(trigger, player["id"]):
                new_role = self._select_new_role(trigger, player["current_role"])
                
                if new_role and new_role != player["current_role"]:
                    mutation = self._perform_mutation(session_id, player["id"], 
                                                    player["current_role"], new_role, trigger)
                    mutations.append(mutation)
        
        return mutations
    
    def get_player_role(self, session_id: int, player_id: int) -> Optional[RoleType]:
        """Get the current role of a player (including mutations)."""
        # Check for active mutation
        if (session_id in self.active_mutations and 
            player_id in self.active_mutations[session_id]):
            return self.active_mutations[session_id][player_id]["current_role"]
        
        # Get from database
        db = SessionLocal()
        try:
            link = db.query(PlayerGameLink).filter(
                PlayerGameLink.session_id == session_id,
                PlayerGameLink.player_id == player_id,
                PlayerGameLink.left_at.is_(None)
            ).first()
            
            if link:
                return RoleType(link.role)
            return None
        finally:
            db.close()
    
    def get_mutation_history(self, session_id: int) -> List[Dict]:
        """Get mutation history for a session."""
        return self.mutation_history.get(session_id, [])
    
    def get_role_info(self, role_type: RoleType) -> Dict:
        """Get information about a specific role."""
        return self.role_definitions.get(role_type, {})
    
    def generate_role_display(self, session_id: int, player_id: int) -> str:
        """Generate a display of the player's current role."""
        role_type = self.get_player_role(session_id, player_id)
        if not role_type:
            return "❌ Role not found"
        
        role_info = self.role_definitions[role_type]
        
        # Check if this is a mutated role
        is_mutated = (session_id in self.active_mutations and 
                     player_id in self.active_mutations[session_id])
        
        display = f"🎭 **Your Role: {role_type.value.title()}**\n\n"
        
        if is_mutated:
            mutation_data = self.active_mutations[session_id][player_id]
            display += f"🔄 **MUTATED** - {mutation_data['description']}\n\n"
        
        display += f"📝 **Description:** {role_info['description']}\n\n"
        display += "🔧 **Abilities:**\n"
        for ability in role_info['abilities']:
            display += f"• {ability}\n"
        
        display += f"\n🎯 **Win Condition:** {role_info['win_condition']}"
        
        return display
    
    def _should_mutate(self, trigger: MutationTrigger, player_id: int) -> bool:
        """Check if a player should mutate based on trigger probability."""
        rule = self.mutation_rules[trigger]
        return random.random() < rule["probability"]
    
    def _select_new_role(self, trigger: MutationTrigger, current_role: RoleType) -> Optional[RoleType]:
        """Select a new role for mutation."""
        rule = self.mutation_rules[trigger]
        allowed_roles = rule["allowed_roles"]
        
        # Filter out current role and get valid options
        valid_roles = [role for role in allowed_roles if role != current_role]
        
        if not valid_roles:
            return None
        
        return random.choice(valid_roles)
    
    def _perform_mutation(self, session_id: int, player_id: int, old_role: RoleType, 
                         new_role: RoleType, trigger: MutationTrigger) -> Dict:
        """Perform the actual role mutation."""
        # Update database
        db = SessionLocal()
        try:
            link = db.query(PlayerGameLink).filter(
                PlayerGameLink.session_id == session_id,
                PlayerGameLink.player_id == player_id,
                PlayerGameLink.left_at.is_(None)
            ).first()
            
            if link:
                link.role = new_role.value
                db.commit()
        except Exception as e:
            logger.error(f"Failed to update role in database: {e}")
            db.rollback()
        finally:
            db.close()
        
        # Store mutation data
        rule = self.mutation_rules[trigger]
        mutation_data = {
            "player_id": player_id,
            "old_role": old_role,
            "new_role": new_role,
            "trigger": trigger,
            "description": rule["description"],
            "timestamp": datetime.now()
        }
        
        self.active_mutations[session_id][player_id] = {
            "current_role": new_role,
            "original_role": old_role,
            "description": rule["description"],
            "mutated_at": datetime.now()
        }
        
        # Add to history
        self.mutation_history[session_id].append(mutation_data)
        
        logger.info(f"Role mutation: Player {player_id} {old_role.value} -> {new_role.value}")
        
        return mutation_data
    
    def _get_active_players(self, session_id: int) -> List[Dict]:
        """Get all active players in a session with their current roles."""
        db = SessionLocal()
        try:
            links = db.query(PlayerGameLink).filter(
                PlayerGameLink.session_id == session_id,
                PlayerGameLink.left_at.is_(None)
            ).all()
            
            players = []
            for link in links:
                # Get current role (including mutations)
                current_role = self.get_player_role(session_id, link.player_id)
                if current_role:
                    players.append({
                        "id": link.player_id,
                        "current_role": current_role
                    })
            
            return players
        finally:
            db.close()
    
    def cleanup_session_mutations(self, session_id: int):
        """Clean up mutations for a finished session."""
        if session_id in self.active_mutations:
            del self.active_mutations[session_id]
        
        if session_id in self.mutation_history:
            del self.mutation_history[session_id]
        
        logger.info(f"Cleaned up mutations for session {session_id}")


# Global instance
mutating_roles_system = MutatingRolesSystem() 