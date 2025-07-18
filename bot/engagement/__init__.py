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
        logger.debug("Initializing EngagementEngine")
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
        logger.debug(f"Processing game completion for player {player_id}")
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
        logger.info(
            f"Processed crate reward for player {player_id}: {summary['crate_reward']}"
        )

        # 2. Update mission progress
        mission_actions = self._get_mission_actions(game_result)
        for action, value in mission_actions.items():
            completed_missions = self.mission_system.update_mission_progress(
                player_id, action, value
            )
            summary["mission_updates"].extend(completed_missions)
        logger.info(
            f"Processed mission updates for player {player_id}: {summary['mission_updates']}"
        )

        # 3. Check for trophy unlocks
        trophy_unlocks = self._check_trophy_unlocks(player_id, game_result)
        summary["trophy_unlocks"] = trophy_unlocks
        logger.info(
            f"Processed trophy unlocks for player {player_id}: {summary['trophy_unlocks']}"
        )

        # 4. Check for title updates
        title_updates = self._check_title_updates(player_id, game_result)
        summary["title_updates"] = title_updates
        logger.info(
            f"Processed title updates for player {player_id}: {summary['title_updates']}"
        )

        # 5. Create shareable result
        share_message = self.shareable_results_system.create_shareable_result(
            player_id, game_result.get("game_id", "unknown"), game_result
        )
        summary["shareable_result"] = share_message
        logger.info(
            f"Processed shareable result for player {player_id}: {summary['shareable_result']}"
        )

        # 6. Calculate total XP gained
        base_xp = game_result.get("xp_gained", 0)
        crate_xp = reward.value if reward.reward_type == RewardType.XP_BOOST else 0
        summary["total_xp_gained"] = base_xp + crate_xp
        logger.info(
            f"Calculated total XP gained for player {player_id}: {summary['total_xp_gained']}"
        )

        logger.info(
            f"Completed game completion processing for player {player_id}: {summary}"
        )

        return summary

    def _get_mission_actions(self, game_result: Dict) -> Dict[str, int]:
        """Extract mission actions from game result."""
        logger.debug(f"Extracting mission actions from game result: {game_result}")
        actions = {}

        # Basic game actions
        actions["games_played"] = 1
        logger.debug(f"Added games_played: {actions['games_played']}")

        if game_result.get("won", False):
            actions["games_won"] = 1
            logger.debug(f"Added games_won: {actions['games_won']}")

            # Check for impostor win
            if game_result.get("role") == "impostor":
                actions["impostor_wins"] = 1
                logger.debug(f"Added impostor_wins: {actions['impostor_wins']}")

        # Task actions
        tasks_completed = game_result.get("tasks_completed", 0)
        if tasks_completed > 0:
            actions["tasks_completed"] = tasks_completed
            logger.debug(f"Added tasks_completed: {actions['tasks_completed']}")

        # Voting actions
        correct_votes = game_result.get("correct_votes", 0)
        if correct_votes > 0:
            actions["correct_votes"] = correct_votes
            logger.debug(f"Added correct_votes: {actions['correct_votes']}")

        logger.debug(f"Final mission actions: {actions}")
        return actions

    def _check_trophy_unlocks(self, player_id: int, game_result: Dict) -> List[Dict]:
        """Check for trophy unlocks based on game result."""
        logger.debug(
            f"Checking trophy unlocks for player {player_id} with game result: {game_result}"
        )
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
                logger.info(f"Unlocked FIRST_WIN trophy for player {player_id}")

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
                logger.info(f"Unlocked MVP trophy for player {player_id}")

        # Task master trophy (check if player has completed 50+ tasks total)
        # This would need to be implemented with database queries
        logger.debug(f"Final trophy unlocks: {unlocks}")
        return unlocks

    def _check_title_updates(self, player_id: int, game_result: Dict) -> List[Dict]:
        """Check for title updates based on game result."""
        logger.debug(
            f"Checking title updates for player {player_id} with game result: {game_result}"
        )
        updates = []

        # Check if player qualifies for new titles
        available_titles = self.status_system.get_available_titles(player_id)
        logger.debug(f"Available titles for player {player_id}: {available_titles}")

        # Get current title
        db = SessionLocal()
        try:
            player = db.query(Player).filter(Player.id == player_id).first()
            if player:
                current_title = player.title
                logger.debug(f"Current title for player {player_id}: {current_title}")

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
                            logger.info(
                                f"Assigned new title {title_name} to player {player_id}"
                            )
        finally:
            db.close()

        logger.debug(f"Final title updates: {updates}")
        return updates

    def generate_engagement_summary(self, player_id: int) -> str:
        """Generate a comprehensive engagement summary for a player."""
        logger.debug(f"Generating engagement summary for player {player_id}")
        summary_parts = []

        # 1. Basecamp display
        basecamp_display = self.basecamp_system.generate_basecamp_display(player_id)
        summary_parts.append(basecamp_display)
        logger.debug(f"Generated basecamp display for player {player_id}")

        # 2. Active missions
        mission_display = self.mission_system.generate_mission_display(player_id)
        summary_parts.append(mission_display)
        logger.debug(f"Generated mission display for player {player_id}")

        # 3. Active wager (if any)
        wager_display = self.risk_reward_system.get_wager_display(player_id)
        if "No active wager" not in wager_display:
            summary_parts.append(wager_display)
            logger.debug(f"Generated wager display for player {player_id}")

        # 4. Card inventory
        card_display = self.betrayal_cards_system.generate_inventory_display(player_id)
        summary_parts.append(card_display)
        logger.debug(f"Generated card inventory display for player {player_id}")

        # 5. Flash events
        flash_display = self.flash_games_system.generate_flash_events_display()
        summary_parts.append(flash_display)
        logger.debug(f"Generated flash events display")

        logger.debug(
            f"Final engagement summary for player {player_id}: {summary_parts}"
        )
        return "\n\n" + "\n\n".join(summary_parts)

    def get_engagement_stats(self, player_id: int) -> Dict:
        """Get comprehensive engagement statistics for a player."""
        logger.debug(f"Getting engagement stats for player {player_id}")
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
        logger.debug(f"Mission stats for player {player_id}: {mission_stats}")

        # Get trophy count
        basecamp = self.basecamp_system.get_player_basecamp(player_id)
        if basecamp:
            stats["trophies_earned"] = basecamp["stats"]["total_trophies"]
            logger.debug(
                f"Trophies earned for player {player_id}: {stats['trophies_earned']}"
            )

        # Get card count
        card_inventory = self.betrayal_cards_system.get_player_inventory(player_id)
        stats["cards_collected"] = sum(card_inventory.values())
        logger.debug(f"Card inventory for player {player_id}: {card_inventory}")

        # Get sharing stats
        sharing_stats = self.shareable_results_system.get_player_sharing_stats(
            player_id
        )
        stats["shares_made"] = sharing_stats["total_shares"]
        logger.debug(f"Sharing stats for player {player_id}: {sharing_stats}")

        logger.debug(f"Final engagement stats for player {player_id}: {stats}")
        return stats

    def cleanup_old_data(self):
        """Clean up old data across all systems."""
        logger.debug("Starting cleanup_old_data")
        # Clean up expired flash events
        self.flash_games_system.cleanup_expired_events()
        logger.debug("Cleaned up expired flash events")

        # Clean up expired seasonal titles
        self.status_system.cleanup_expired_seasonal_titles()
        logger.debug("Cleaned up expired seasonal titles")

        # Clean up old shareable results
        self.shareable_results_system.cleanup_old_results()
        logger.debug("Cleaned up old shareable results")

        # Clean up expired missions
        # This is handled automatically in the mission system
        logger.debug("Finished cleanup_old_data")


# Global instance
engagement_engine = EngagementEngine()
