"""
Mission System - Daily/weekly missions with commitment loops and streaks.
"""

import random
from typing import Dict, List, Optional, Tuple
from enum import Enum
from datetime import datetime, timedelta
from bot.database import SessionLocal
from bot.database.models import Player
import logging

logger = logging.getLogger(__name__)


class MissionType(Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    SEASONAL = "seasonal"
    SPECIAL = "special"


class MissionCategory(Enum):
    GAMEPLAY = "gameplay"
    SOCIAL = "social"
    ACHIEVEMENT = "achievement"
    COLLECTION = "collection"


class Mission:
    """Represents a mission/quest."""
    
    def __init__(self, mission_id: str, name: str, description: str, 
                 mission_type: MissionType, category: MissionCategory,
                 requirements: Dict, rewards: Dict, duration_days: int = 1):
        self.mission_id = mission_id
        self.name = name
        self.description = description
        self.mission_type = mission_type
        self.category = category
        self.requirements = requirements
        self.rewards = rewards
        self.duration_days = duration_days
        self.emoji = self._get_mission_emoji(category)
    
    def _get_mission_emoji(self, category: MissionCategory) -> str:
        """Get emoji for mission category."""
        emojis = {
            MissionCategory.GAMEPLAY: "🎮",
            MissionCategory.SOCIAL: "👥",
            MissionCategory.ACHIEVEMENT: "🏆",
            MissionCategory.COLLECTION: "📦"
        }
        return emojis.get(category, "📋")


class MissionSystem:
    """Manages daily/weekly missions and streaks."""
    
    def __init__(self):
        # Mission templates
        self.mission_templates = {
            # Daily missions
            "daily_play_3_games": Mission(
                "daily_play_3_games", "Game Master", "Play 3 games today",
                MissionType.DAILY, MissionCategory.GAMEPLAY,
                {"games_played": 3}, {"xp": 25, "badge": "daily_player"}, 1
            ),
            "daily_win_1_game": Mission(
                "daily_win_1_game", "Victory Lap", "Win 1 game today",
                MissionType.DAILY, MissionCategory.GAMEPLAY,
                {"games_won": 1}, {"xp": 50, "badge": "daily_winner"}, 1
            ),
            "daily_complete_5_tasks": Mission(
                "daily_complete_5_tasks", "Task Force", "Complete 5 tasks today",
                MissionType.DAILY, MissionCategory.GAMEPLAY,
                {"tasks_completed": 5}, {"xp": 30, "badge": "task_master"}, 1
            ),
            "daily_vote_correctly": Mission(
                "daily_vote_correctly", "Sharp Eye", "Vote correctly 2 times today",
                MissionType.DAILY, MissionCategory.GAMEPLAY,
                {"correct_votes": 2}, {"xp": 20, "badge": "voter"}, 1
            ),
            
            # Weekly missions
            "weekly_play_15_games": Mission(
                "weekly_play_15_games", "Dedicated Player", "Play 15 games this week",
                MissionType.WEEKLY, MissionCategory.GAMEPLAY,
                {"games_played": 15}, {"xp": 100, "badge": "dedicated"}, 7
            ),
            "weekly_win_5_games": Mission(
                "weekly_win_5_games", "Weekend Warrior", "Win 5 games this week",
                MissionType.WEEKLY, MissionCategory.GAMEPLAY,
                {"games_won": 5}, {"xp": 150, "badge": "warrior"}, 7
            ),
            "weekly_complete_25_tasks": Mission(
                "weekly_complete_25_tasks", "Task Champion", "Complete 25 tasks this week",
                MissionType.WEEKLY, MissionCategory.GAMEPLAY,
                {"tasks_completed": 25}, {"xp": 120, "badge": "champion"}, 7
            ),
            "weekly_win_as_impostor": Mission(
                "weekly_win_as_impostor", "Deception Master", "Win 3 times as impostor this week",
                MissionType.WEEKLY, MissionCategory.GAMEPLAY,
                {"impostor_wins": 3}, {"xp": 200, "badge": "deceiver"}, 7
            ),
            
            # Seasonal missions
            "seasonal_halloween": Mission(
                "seasonal_halloween", "🎃 Spooky Season", "Win 10 games during October",
                MissionType.SEASONAL, MissionCategory.ACHIEVEMENT,
                {"seasonal_wins": 10, "season": "october"}, {"xp": 500, "title": "🎃 Ghost of October"}, 31
            ),
            "seasonal_winter": Mission(
                "seasonal_winter", "❄️ Winter Wonderland", "Win 10 games during December",
                MissionType.SEASONAL, MissionCategory.ACHIEVEMENT,
                {"seasonal_wins": 10, "season": "december"}, {"xp": 500, "title": "❄️ Winter Guardian"}, 31
            ),
        }
        
        # Track active missions: {player_id: {mission_id: MissionProgress}}
        self.active_missions = {}
        
        # Track streaks: {player_id: {mission_type: streak_count}}
        self.streaks = {}
    
    def assign_daily_missions(self, player_id: int) -> List[Mission]:
        """Assign daily missions to a player."""
        if player_id not in self.active_missions:
            self.active_missions[player_id] = {}
        
        # Get daily mission templates
        daily_templates = [m for m in self.mission_templates.values() 
                         if m.mission_type == MissionType.DAILY]
        
        # Randomly select 3 daily missions
        selected_missions = random.sample(daily_templates, min(3, len(daily_templates)))
        
        assigned_missions = []
        for mission in selected_missions:
            mission_progress = {
                "mission": mission,
                "progress": 0,
                "completed": False,
                "assigned_at": datetime.now(),
                "expires_at": datetime.now() + timedelta(days=mission.duration_days)
            }
            
            self.active_missions[player_id][mission.mission_id] = mission_progress
            assigned_missions.append(mission)
        
        logger.info(f"Assigned {len(assigned_missions)} daily missions to player {player_id}")
        return assigned_missions
    
    def assign_weekly_missions(self, player_id: int) -> List[Mission]:
        """Assign weekly missions to a player."""
        if player_id not in self.active_missions:
            self.active_missions[player_id] = {}
        
        # Get weekly mission templates
        weekly_templates = [m for m in self.mission_templates.values() 
                          if m.mission_type == MissionType.WEEKLY]
        
        # Randomly select 2 weekly missions
        selected_missions = random.sample(weekly_templates, min(2, len(weekly_templates)))
        
        assigned_missions = []
        for mission in selected_missions:
            mission_progress = {
                "mission": mission,
                "progress": 0,
                "completed": False,
                "assigned_at": datetime.now(),
                "expires_at": datetime.now() + timedelta(days=mission.duration_days)
            }
            
            self.active_missions[player_id][mission.mission_id] = mission_progress
            assigned_missions.append(mission)
        
        logger.info(f"Assigned {len(assigned_missions)} weekly missions to player {player_id}")
        return assigned_missions
    
    def update_mission_progress(self, player_id: int, action: str, value: int = 1) -> List[Dict]:
        """Update mission progress for a player."""
        if player_id not in self.active_missions:
            return []
        
        completed_missions = []
        
        for mission_id, progress in self.active_missions[player_id].items():
            if progress["completed"]:
                continue
            
            mission = progress["mission"]
            requirements = mission.requirements
            
            # Check if this action affects this mission
            if action in requirements:
                progress["progress"] += value
                
                # Check if mission is completed
                if progress["progress"] >= requirements[action]:
                    progress["completed"] = True
                    completed_missions.append({
                        "mission": mission,
                        "rewards": mission.rewards,
                        "progress": progress["progress"]
                    })
                    
                    logger.info(f"Player {player_id} completed mission: {mission.name}")
        
        return completed_missions
    
    def claim_mission_rewards(self, player_id: int, mission_id: str) -> Tuple[bool, str]:
        """Claim rewards for a completed mission."""
        if (player_id not in self.active_missions or 
            mission_id not in self.active_missions[player_id]):
            return False, "❌ Mission not found."
        
        progress = self.active_missions[player_id][mission_id]
        if not progress["completed"]:
            return False, "❌ Mission not completed yet."
        
        if progress.get("claimed", False):
            return False, "❌ Rewards already claimed."
        
        # Apply rewards
        db = SessionLocal()
        try:
            player = db.query(Player).filter(Player.id == player_id).first()
            if not player:
                return False, "❌ Player not found."
            
            rewards = progress["mission"].rewards
            
            # Apply XP reward
            if "xp" in rewards:
                player.xp += rewards["xp"]
            
            # Apply badge reward (would need badge system)
            if "badge" in rewards:
                logger.info(f"Player {player_id} earned badge: {rewards['badge']}")
            
            # Apply title reward
            if "title" in rewards:
                player.title = rewards["title"]
            
            db.commit()
            
            # Mark as claimed
            progress["claimed"] = True
            
            # Update streak
            self._update_streak(player_id, progress["mission"].mission_type)
            
            reward_text = f"✨ **+{rewards.get('xp', 0)} XP**"
            if "badge" in rewards:
                reward_text += f"\n🏆 **Badge:** {rewards['badge']}"
            if "title" in rewards:
                reward_text += f"\n🏷️ **Title:** {rewards['title']}"
            
            return True, (
                f"🎉 **Mission Completed!**\n\n"
                f"📋 **{progress['mission'].name}**\n"
                f"📝 {progress['mission'].description}\n\n"
                f"🎁 **Rewards:**\n{reward_text}"
            )
            
        except Exception as e:
            logger.error(f"Failed to claim mission rewards: {e}")
            db.rollback()
            return False, "❌ Failed to claim rewards."
        finally:
            db.close()
    
    def get_player_missions(self, player_id: int) -> Dict[str, Dict]:
        """Get all missions for a player."""
        if player_id not in self.active_missions:
            return {}
        
        # Clean up expired missions
        self._cleanup_expired_missions(player_id)
        
        return self.active_missions[player_id]
    
    def _cleanup_expired_missions(self, player_id: int):
        """Remove expired missions."""
        if player_id not in self.active_missions:
            return
        
        current_time = datetime.now()
        expired_missions = []
        
        for mission_id, progress in self.active_missions[player_id].items():
            if progress["expires_at"] < current_time and not progress["completed"]:
                expired_missions.append(mission_id)
        
        for mission_id in expired_missions:
            del self.active_missions[player_id][mission_id]
        
        if expired_missions:
            logger.info(f"Cleaned up {len(expired_missions)} expired missions for player {player_id}")
    
    def _update_streak(self, player_id: int, mission_type: MissionType):
        """Update mission completion streak."""
        if player_id not in self.streaks:
            self.streaks[player_id] = {}
        
        if mission_type.value not in self.streaks[player_id]:
            self.streaks[player_id][mission_type.value] = 0
        
        self.streaks[player_id][mission_type.value] += 1
    
    def get_streak_info(self, player_id: int) -> Dict:
        """Get streak information for a player."""
        if player_id not in self.streaks:
            return {}
        
        return self.streaks[player_id]
    
    def generate_mission_display(self, player_id: int) -> str:
        """Generate a display of player's missions."""
        missions = self.get_player_missions(player_id)
        
        if not missions:
            return "📋 **No active missions**\n\nComplete games to get daily and weekly missions!"
        
        display = "📋 **Your Missions**\n\n"
        
        # Group by type
        daily_missions = []
        weekly_missions = []
        
        for mission_id, progress in missions.items():
            mission = progress["mission"]
            if mission.mission_type == MissionType.DAILY:
                daily_missions.append((mission, progress))
            elif mission.mission_type == MissionType.WEEKLY:
                weekly_missions.append((mission, progress))
        
        # Display daily missions
        if daily_missions:
            display += "📅 **Daily Missions:**\n"
            for mission, progress in daily_missions:
                status = "✅" if progress["completed"] else "⏳"
                display += (
                    f"{status} **{mission.name}**\n"
                    f"   📝 {mission.description}\n"
                    f"   📊 Progress: {progress['progress']}/{mission.requirements.get(list(mission.requirements.keys())[0], 0)}\n\n"
                )
        
        # Display weekly missions
        if weekly_missions:
            display += "📆 **Weekly Missions:**\n"
            for mission, progress in weekly_missions:
                status = "✅" if progress["completed"] else "⏳"
                display += (
                    f"{status} **{mission.name}**\n"
                    f"   📝 {mission.description}\n"
                    f"   📊 Progress: {progress['progress']}/{mission.requirements.get(list(mission.requirements.keys())[0], 0)}\n\n"
                )
        
        return display


# Global instance
mission_system = MissionSystem() 