"""
Engagement Engine - Main integration for all engagement systems.
"""

from typing import Dict, List
from .crate_system import crate_system, CrateType, RewardType
from .status_system import status_system, TitleRarity
from .basecamp_system import basecamp_system, RoomTheme, TrophyType
from .risk_reward_system import risk_reward_system, WagerType
from .mission_system import mission_system, MissionType, MissionCategory
from .flash_games_system import flash_games_system, FlashEventType
from .betrayal_cards_system import betrayal_cards_system, CardType
from .shareable_results_system import shareable_results_system
from bot.database.models import Player
from bot.database import SessionLocal

import logging

logger = logging.getLogger(__name__)


class EngagementEngine:
    """
    Main engagement engine that orchestrates all engagement systems.
    """

    def __init__(self):
        self.crate_system = crate_system
        self.status_system = status_system
        self.basecamp_system = basecamp_system
        self.risk_reward_system = risk_reward_system
        self.mission_system = mission_system
        self.flash_games_system = flash_games_system
        self.betrayal_cards_system = betrayal_cards_system
        self.shareable_results_system = shareable_results_system

    def process_game_completion(self, player_id: int, game_result: Dict) -> Dict:
        """
        Process all engagement mechanics when a game completes.
        Returns a comprehensive summary of all rewards and achievements.
        """
        summary = {
            "crate_reward": None,
            "mission_updates": [],
            "trophy_unlocks": [],
            "title_updates": [],
            "shareable_result": None,
            "total_xp_gained": 0,
        }

        # 1. Determine crate type and open it
        crate_type = self.crate_system.determine_crate_type(game_result)
        reward, message = self.crate_system.open_crate(crate_type, player_id)
        summary["crate_reward"] = {
            "crate_type": crate_type.value,
            "reward": reward.description,
            "rarity": reward.rarity,
            "message": message,
        }

        # 2. Update mission progress
        mission_actions = self._get_mission_actions(game_result)
        for action, value in mission_actions.items():
            completed_missions = self.mission_system.update_mission_progress(
                player_id, action, value
            )
            summary["mission_updates"].extend(completed_missions)

        # 3. Check for trophy unlocks
        trophy_unlocks = self._check_trophy_unlocks(player_id, game_result)
        summary["trophy_unlocks"] = trophy_unlocks

        # 4. Check for title updates
        title_updates = self._check_title_updates(player_id, game_result)
        summary["title_updates"] = title_updates

        # 5. Create shareable result
        share_message = self.shareable_results_system.create_shareable_result(
            player_id, game_result.get("game_id", "unknown"), game_result
        )
        summary["shareable_result"] = share_message

        # 6. Calculate total XP gained
        base_xp = game_result.get("xp_gained", 0)
        crate_xp = reward.value if reward.reward_type == RewardType.XP_BOOST else 0
        summary["total_xp_gained"] = base_xp + crate_xp

        logger.info(f"Processed game completion for player {player_id}: {summary}")

        return summary

    def _get_mission_actions(self, game_result: Dict) -> Dict[str, int]:
        """Extract mission actions from game result."""
        actions = {}

        # Basic game actions
        actions["games_played"] = 1

        if game_result.get("won", False):
            actions["games_won"] = 1

            # Check for impostor win
            if game_result.get("role") == "impostor":
                actions["impostor_wins"] = 1

        # Task actions
        tasks_completed = game_result.get("tasks_completed", 0)
        if tasks_completed > 0:
            actions["tasks_completed"] = tasks_completed

        # Voting actions
        correct_votes = game_result.get("correct_votes", 0)
        if correct_votes > 0:
            actions["correct_votes"] = correct_votes

        return actions

    def _check_trophy_unlocks(self, player_id: int, game_result: Dict) -> List[Dict]:
        """Check for trophy unlocks based on game result."""
        unlocks = []

        # First win trophy
        if game_result.get("won", False) and game_result.get("first_win", False):
            trophy = self.basecamp_system.unlock_trophy(player_id, TrophyType.FIRST_WIN)
            if trophy:
                unlocks.append(
                    {
                        "trophy_name": trophy.name,
                        "description": trophy.description,
                        "emoji": trophy.emoji,
                        "rarity": trophy.rarity,
                    }
                )

        # MVP trophy
        if game_result.get("mvp", False):
            trophy = self.basecamp_system.unlock_trophy(player_id, TrophyType.MVP)
            if trophy:
                unlocks.append(
                    {
                        "trophy_name": trophy.name,
                        "description": trophy.description,
                        "emoji": trophy.emoji,
                        "rarity": trophy.rarity,
                    }
                )

        # Task master trophy (check if player has completed 50+ tasks total)
        # This would need to be implemented with database queries

        return unlocks

    def _check_title_updates(self, player_id: int, game_result: Dict) -> List[Dict]:
        """Check for title updates based on game result."""
        updates = []

        # Check if player qualifies for new titles
        available_titles = self.status_system.get_available_titles(player_id)

        # Get current title
        db = SessionLocal()
        try:
            player = db.query(Player).filter(Player.id == player_id).first()
            if player:
                current_title = player.title

                # Check for new titles
                for title_name in available_titles:
                    if title_name != current_title:
                        # Assign new title
                        if self.status_system.assign_title(player_id, title_name):
                            title_info = self.status_system.get_title_info(title_name)
                            updates.append(
                                {
                                    "old_title": current_title,
                                    "new_title": title_name,
                                    "rarity": (
                                        title_info.get("rarity", "common")
                                        if title_info
                                        else "common"
                                    ),
                                }
                            )
        finally:
            db.close()

        return updates

    def generate_engagement_summary(self, player_id: int) -> str:
        """Generate a comprehensive engagement summary for a player."""
        summary_parts = []

        # 1. Basecamp display
        basecamp_display = self.basecamp_system.generate_basecamp_display(player_id)
        summary_parts.append(basecamp_display)

        # 2. Active missions
        mission_display = self.mission_system.generate_mission_display(player_id)
        summary_parts.append(mission_display)

        # 3. Active wager (if any)
        wager_display = self.risk_reward_system.get_wager_display(player_id)
        if "No active wager" not in wager_display:
            summary_parts.append(wager_display)

        # 4. Card inventory
        card_display = self.betrayal_cards_system.generate_inventory_display(player_id)
        summary_parts.append(card_display)

        # 5. Flash events
        flash_display = self.flash_games_system.generate_flash_events_display()
        summary_parts.append(flash_display)

        return "\n\n" + "\n\n".join(summary_parts)

    def get_engagement_stats(self, player_id: int) -> Dict:
        """Get comprehensive engagement statistics for a player."""
        stats = {
            "crates_opened": 0,  # Would need to track this
            "missions_completed": 0,
            "trophies_earned": 0,
            "cards_collected": 0,
            "wagers_placed": 0,
            "shares_made": 0,
            "flash_events_joined": 0,
        }

        # Get mission stats
        mission_stats = self.mission_system.get_streak_info(player_id)
        stats["missions_completed"] = sum(mission_stats.values())

        # Get trophy count
        basecamp = self.basecamp_system.get_player_basecamp(player_id)
        if basecamp:
            stats["trophies_earned"] = basecamp["stats"]["total_trophies"]

        # Get card count
        card_inventory = self.betrayal_cards_system.get_player_inventory(player_id)
        stats["cards_collected"] = sum(card_inventory.values())

        # Get sharing stats
        sharing_stats = self.shareable_results_system.get_player_sharing_stats(
            player_id
        )
        stats["shares_made"] = sharing_stats["total_shares"]

        return stats

    def cleanup_old_data(self):
        """Clean up old data across all systems."""
        # Clean up expired flash events
        self.flash_games_system.cleanup_expired_events()

        # Clean up expired seasonal titles
        self.status_system.cleanup_expired_seasonal_titles()

        # Clean up old shareable results
        self.shareable_results_system.cleanup_old_results()

        # Clean up expired missions
        # This is handled automatically in the mission system

        logger.info("Cleaned up old engagement data")


# Global instance
engagement_engine = EngagementEngine()
