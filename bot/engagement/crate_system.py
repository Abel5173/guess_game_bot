"""
Mystery Crate System - Variable Rewards with Skinner Box Mechanics
"""

import random
from typing import Dict, List, Optional, Tuple
from enum import Enum
from datetime import datetime, timedelta
from bot.database import SessionLocal
from bot.database.models import Player
import logging

logger = logging.getLogger(__name__)


class CrateType(Enum):
    """Crate rarity types with different reward probabilities."""

    BRONZE = "bronze"
    SILVER = "silver"
    GOLD = "gold"
    MYTHIC = "mythic"  # Ultra rare


class RewardType(Enum):
    """Types of rewards that can be found in crates."""

    XP_BOOST = "xp_boost"
    COSMETIC_BADGE = "cosmetic_badge"
    SECRET_ROLE = "secret_role"
    BETRAYAL_CARD = "betrayal_card"
    TITLE_UNLOCK = "title_unlock"
    NOTHING = "nothing"  # Empty crate for unpredictability


class Reward:
    """Represents a reward from a crate."""

    def __init__(
        self, reward_type: RewardType, value: int, description: str, rarity: str
    ):
        self.reward_type = reward_type
        self.value = value
        self.description = description
        self.rarity = rarity  # common, rare, epic, legendary

    def __str__(self):
        return f"{self.description} ({self.rarity})"


class CrateSystem:
    """Manages the mystery crate system with variable rewards."""

    def __init__(self):
        self.crate_rewards = {
            CrateType.BRONZE: {
                RewardType.XP_BOOST: {"weight": 60, "min": 10, "max": 25},
                RewardType.COSMETIC_BADGE: {"weight": 30, "min": 1, "max": 1},
                RewardType.NOTHING: {"weight": 10, "min": 0, "max": 0},
            },
            CrateType.SILVER: {
                RewardType.XP_BOOST: {"weight": 50, "min": 25, "max": 50},
                RewardType.COSMETIC_BADGE: {"weight": 35, "min": 1, "max": 2},
                RewardType.SECRET_ROLE: {"weight": 10, "min": 1, "max": 1},
                RewardType.BETRAYAL_CARD: {"weight": 5, "min": 1, "max": 1},
            },
            CrateType.GOLD: {
                RewardType.XP_BOOST: {"weight": 40, "min": 50, "max": 100},
                RewardType.COSMETIC_BADGE: {"weight": 30, "min": 2, "max": 3},
                RewardType.SECRET_ROLE: {"weight": 20, "min": 1, "max": 1},
                RewardType.TITLE_UNLOCK: {"weight": 10, "min": 1, "max": 1},
            },
            CrateType.MYTHIC: {
                RewardType.XP_BOOST: {"weight": 30, "min": 100, "max": 200},
                RewardType.COSMETIC_BADGE: {"weight": 25, "min": 3, "max": 5},
                RewardType.SECRET_ROLE: {"weight": 25, "min": 1, "max": 1},
                RewardType.TITLE_UNLOCK: {"weight": 20, "min": 1, "max": 1},
            },
        }

        self.badge_descriptions = {
            "detective": "🕵️ Detective Badge",
            "survivor": "🛡️ Survivor Badge",
            "impostor": "🎭 Impostor Badge",
            "mvp": "🏆 MVP Badge",
            "streak": "🔥 Streak Badge",
            "veteran": "⭐ Veteran Badge",
            "lucky": "🍀 Lucky Badge",
            "strategist": "🧠 Strategist Badge",
        }

        self.secret_roles = {
            "detective": "🕵️ Detective (Can see one player's role)",
            "guardian": "🛡️ Guardian (Protects one player from ejection)",
            "saboteur": "💣 Saboteur (Can sabotage one vote)",
            "oracle": "🔮 Oracle (Gets one hint about the impostor)",
        }

        self.betrayal_cards = {
            "fake_task": "🎯 Fake Task (Complete a fake task for bonus XP)",
            "double_vote": "🗳️ Double Vote (Your vote counts twice)",
            "anonymous_vote": "👻 Anonymous Vote (Vote without revealing)",
            "sabotage": "💥 Sabotage (Remove one player's vote)",
            "whisper": "🤫 Whisper (Send one secret message)",
        }

    def determine_crate_type(self, game_result: Dict) -> CrateType:
        """Determine crate type based on game performance."""
        # Base on win/loss
        if game_result.get("won", False):
            # Winning players get better crates
            if game_result.get("mvp", False):
                return CrateType.MYTHIC
            elif game_result.get("tasks_completed", 0) >= 3:
                return CrateType.GOLD
            else:
                return CrateType.SILVER
        else:
            # Losing players still get something (engagement!)
            if game_result.get("tasks_completed", 0) >= 2:
                return CrateType.SILVER
            else:
                return CrateType.BRONZE

    def open_crate(self, crate_type: CrateType, player_id: int) -> Tuple[Reward, str]:
        """Open a crate and return the reward with a dramatic message."""
        # Get possible rewards for this crate type
        possible_rewards = self.crate_rewards[crate_type]

        # Weighted random selection
        total_weight = sum(reward["weight"] for reward in possible_rewards.values())
        roll = random.randint(1, total_weight)

        current_weight = 0
        selected_reward_type = None

        for reward_type, config in possible_rewards.items():
            current_weight += config["weight"]
            if roll <= current_weight:
                selected_reward_type = reward_type
                break

        if not selected_reward_type:
            selected_reward_type = RewardType.NOTHING

        # Generate the reward
        reward = self._generate_reward(selected_reward_type, crate_type)

        # Create dramatic message
        message = self._create_crate_message(crate_type, reward)

        # Apply the reward to the player
        self._apply_reward(player_id, reward)

        return reward, message

    def _generate_reward(
        self, reward_type: RewardType, crate_type: CrateType
    ) -> Reward:
        """Generate a specific reward based on type and crate."""
        config = self.crate_rewards[crate_type][reward_type]

        if reward_type == RewardType.XP_BOOST:
            value = random.randint(config["min"], config["max"])
            return Reward(
                reward_type=reward_type,
                value=value,
                description=f"🔥 +{value} XP Boost",
                rarity="common" if value < 50 else "rare" if value < 100 else "epic",
            )

        elif reward_type == RewardType.COSMETIC_BADGE:
            badge_name = random.choice(list(self.badge_descriptions.keys()))
            return Reward(
                reward_type=reward_type,
                value=config["min"],
                description=self.badge_descriptions[badge_name],
                rarity="common",
            )

        elif reward_type == RewardType.SECRET_ROLE:
            role_name = random.choice(list(self.secret_roles.keys()))
            return Reward(
                reward_type=reward_type,
                value=1,
                description=self.secret_roles[role_name],
                rarity="epic",
            )

        elif reward_type == RewardType.BETRAYAL_CARD:
            card_name = random.choice(list(self.betrayal_cards.keys()))
            return Reward(
                reward_type=reward_type,
                value=1,
                description=self.betrayal_cards[card_name],
                rarity="rare",
            )

        elif reward_type == RewardType.TITLE_UNLOCK:
            # Generate a unique title
            titles = ["Shadow Master", "Ghost Whisperer", "Void Walker", "Echo Seeker"]
            title = random.choice(titles)
            return Reward(
                reward_type=reward_type,
                value=1,
                description=f"👑 {title} Title",
                rarity="legendary",
            )

        else:  # NOTHING
            return Reward(
                reward_type=reward_type,
                value=0,
                description="💨 Empty Crate",
                rarity="common",
            )

    def _create_crate_message(self, crate_type: CrateType, reward: Reward) -> str:
        """Create a dramatic crate opening message."""
        crate_emojis = {
            CrateType.BRONZE: "📦",
            CrateType.SILVER: "🥈",
            CrateType.GOLD: "🥇",
            CrateType.MYTHIC: "💎",
        }

        crate_emoji = crate_emojis[crate_type]

        if reward.reward_type == RewardType.NOTHING:
            return f"{crate_emoji} **{crate_type.value.title()} Crate**\n💨 *The crate was empty... Better luck next time!*"

        rarity_emojis = {"common": "⚪", "rare": "🔵", "epic": "🟣", "legendary": "🟡"}

        rarity_emoji = rarity_emojis.get(reward.rarity, "⚪")

        return (
            f"{crate_emoji} **{crate_type.value.title()} Crate**\n"
            f"{rarity_emoji} **{reward.description}**\n"
            f"🎉 *You found something amazing!*"
        )

    def _apply_reward(self, player_id: int, reward: Reward):
        """Apply the reward to the player's account."""
        db = SessionLocal()
        try:
            player = db.query(Player).filter(Player.id == player_id).first()
            if not player:
                return

            if reward.reward_type == RewardType.XP_BOOST:
                player.xp += reward.value
                logger.info(f"Player {player_id} gained {reward.value} XP from crate")

            elif reward.reward_type == RewardType.COSMETIC_BADGE:
                # Add badge to player's badges (JSON field)
                current_badges = player.badges or {}
                badge_name = reward.description.split()[1].lower()
                current_badges[badge_name] = current_badges.get(badge_name, 0) + 1
                player.badges = current_badges
                logger.info(f"Player {player_id} unlocked badge: {badge_name}")

            elif reward.reward_type == RewardType.TITLE_UNLOCK:
                # Add title to available titles
                title_name = reward.description.split()[1:]
                if player.title == "Rookie":
                    player.title = " ".join(title_name)
                    logger.info(f"Player {player_id} unlocked title: {player.title}")

            db.commit()

        except Exception as e:
            logger.error(f"Failed to apply reward to player {player_id}: {e}")
            db.rollback()
        finally:
            db.close()

    def get_player_crates_opened(self, player_id: int) -> Dict[str, int]:
        """Get statistics about crates opened by a player."""
        # This would need to be tracked in the database
        # For now, return placeholder data
        return {"bronze": 0, "silver": 0, "gold": 0, "mythic": 0, "total": 0}


# Global instance
crate_system = CrateSystem()
