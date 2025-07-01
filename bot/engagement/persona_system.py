"""
Persona Challenges System - Role-playing mechanics for enhanced gameplay.
"""

import random
from typing import Dict, List, Optional, Tuple
from enum import Enum
from datetime import datetime, timedelta
from bot.database import SessionLocal
from bot.database.models import Player, DiscussionLog
import logging

logger = logging.getLogger(__name__)


class PersonaType(Enum):
    DETECTIVE = "detective"
    PARANOID = "paranoid"
    CHARMER = "charmer"
    SILENT = "silent"
    LEADER = "leader"
    REBEL = "rebel"
    MEDIATOR = "mediator"
    TRICKSTER = "trickster"


class PersonaSystem:
    """Manages persona challenges and role-playing mechanics."""
    
    def __init__(self):
        self.active_challenges = {}  # session_id -> {player_id -> PersonaChallenge}
        self.challenge_progress = {}  # session_id -> {player_id -> progress_data}
        self.persona_definitions = {
            PersonaType.DETECTIVE: {
                "description": "You are a brilliant detective. Use logic and evidence.",
                "rules": ["Ask questions", "Reference evidence", "Use logical reasoning"],
                "bonus_xp": 50,
                "difficulty": "medium"
            },
            PersonaType.PARANOID: {
                "description": "You are extremely paranoid. Trust no one.",
                "rules": ["Accuse multiple players", "Express distrust", "Question motives"],
                "bonus_xp": 40,
                "difficulty": "easy"
            },
            PersonaType.CHARMER: {
                "description": "You are charismatic. Sway others with charm.",
                "rules": ["Use positive language", "Defend players", "Unite the group"],
                "bonus_xp": 60,
                "difficulty": "hard"
            },
            PersonaType.SILENT: {
                "description": "You are the silent observer. Speak only when necessary.",
                "rules": ["Keep messages short", "Speak only when addressed", "Be cryptic"],
                "bonus_xp": 30,
                "difficulty": "easy"
            }
        }
    
    def assign_persona_challenge(self, session_id: int, player_id: int, 
                               persona_type: PersonaType = None) -> Dict:
        """Assign a persona challenge to a player."""
        if persona_type is None:
            persona_type = random.choice(list(PersonaType))
        
        challenge = self.persona_definitions[persona_type]
        
        if session_id not in self.active_challenges:
            self.active_challenges[session_id] = {}
        
        self.active_challenges[session_id][player_id] = {
            "type": persona_type,
            **challenge
        }
        
        # Initialize progress tracking
        if session_id not in self.challenge_progress:
            self.challenge_progress[session_id] = {}
        
        self.challenge_progress[session_id][player_id] = {
            "assigned_at": datetime.now(),
            "total_messages": 0,
            "persona_messages": 0
        }
        
        return self.active_challenges[session_id][player_id]
    
    def analyze_message(self, session_id: int, player_id: int, message: str) -> Dict:
        """Analyze a player's message for persona compliance."""
        challenge = self.get_player_challenge(session_id, player_id)
        if not challenge:
            return {"compliance": 0, "feedback": "No active persona challenge"}
        
        progress = self.challenge_progress[session_id][player_id]
        progress["total_messages"] += 1
        
        compliance_score = 0
        feedback = []
        
        persona_type = challenge["type"]
        
        if persona_type == PersonaType.DETECTIVE:
            if any(phrase in message.lower() for phrase in ["evidence", "analyze", "based on"]):
                compliance_score += 1
                feedback.append("✅ Good detective work!")
        
        elif persona_type == PersonaType.PARANOID:
            if any(phrase in message.lower() for phrase in ["suspicious", "don't trust", "everyone"]):
                compliance_score += 1
                feedback.append("✅ Staying appropriately paranoid!")
        
        elif persona_type == PersonaType.CHARMER:
            if any(phrase in message.lower() for phrase in ["believe", "trust", "together"]):
                compliance_score += 1
                feedback.append("✅ Using your charm effectively!")
        
        elif persona_type == PersonaType.SILENT:
            if len(message.split()) <= 20:
                compliance_score += 1
                feedback.append("✅ Keeping it brief and mysterious!")
        
        if compliance_score > 0:
            progress["persona_messages"] += 1
        
        return {
            "compliance": compliance_score,
            "feedback": " ".join(feedback) if feedback else "Keep working on your persona!",
            "persona_type": persona_type.value
        }
    
    def get_player_challenge(self, session_id: int, player_id: int) -> Optional[Dict]:
        """Get the current persona challenge for a player."""
        if (session_id in self.active_challenges and 
            player_id in self.active_challenges[session_id]):
            return self.active_challenges[session_id][player_id]
        return None
    
    def get_challenge_progress(self, session_id: int, player_id: int) -> Dict:
        """Get progress on current persona challenge."""
        challenge = self.get_player_challenge(session_id, player_id)
        if not challenge:
            return {"error": "No active persona challenge"}
        
        progress = self.challenge_progress[session_id][player_id]
        total_messages = progress["total_messages"]
        persona_messages = progress["persona_messages"]
        
        compliance_rate = (persona_messages / total_messages * 100) if total_messages > 0 else 0
        
        return {
            "persona_type": challenge["type"].value,
            "description": challenge["description"],
            "difficulty": challenge["difficulty"],
            "bonus_xp": challenge["bonus_xp"],
            "total_messages": total_messages,
            "persona_messages": persona_messages,
            "compliance_rate": round(compliance_rate, 1),
            "rules": challenge["rules"]
        }
    
    def complete_challenge(self, session_id: int, player_id: int) -> Tuple[bool, int]:
        """Complete a persona challenge and award bonus XP."""
        challenge = self.get_player_challenge(session_id, player_id)
        if not challenge:
            return False, 0
        
        progress = self.challenge_progress[session_id][player_id]
        compliance_rate = (progress["persona_messages"] / progress["total_messages"] * 100) if progress["total_messages"] > 0 else 0
        
        # Award XP based on compliance rate
        if compliance_rate >= 60:
            bonus_xp = challenge["bonus_xp"]
            success = True
        else:
            bonus_xp = 0
            success = False
        
        # Apply XP to player
        if success:
            self._award_persona_xp(player_id, bonus_xp)
        
        # Clean up challenge
        self._cleanup_challenge(session_id, player_id)
        
        return success, bonus_xp
    
    def _award_persona_xp(self, player_id: int, bonus_xp: int):
        """Award bonus XP for persona challenge completion."""
        db = SessionLocal()
        try:
            player = db.query(Player).filter(Player.id == player_id).first()
            if player:
                player.xp += bonus_xp
                db.commit()
        except Exception as e:
            logger.error(f"Failed to award persona XP: {e}")
            db.rollback()
        finally:
            db.close()
    
    def _cleanup_challenge(self, session_id: int, player_id: int):
        """Clean up completed persona challenge."""
        if session_id in self.active_challenges:
            self.active_challenges[session_id].pop(player_id, None)
        
        if session_id in self.challenge_progress:
            self.challenge_progress[session_id].pop(player_id, None)
    
    def cleanup_session_personas(self, session_id: int):
        """Clean up all persona challenges for a finished session."""
        if session_id in self.active_challenges:
            del self.active_challenges[session_id]
        
        if session_id in self.challenge_progress:
            del self.challenge_progress[session_id]


# Global instance
persona_system = PersonaSystem() 