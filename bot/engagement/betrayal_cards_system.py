"""
Betrayal Cards System - Emergent gameplay mechanics and power-ups.
"""

import random
from typing import Dict, List, Optional, Tuple
from enum import Enum
from datetime import datetime
from bot.database import SessionLocal
from bot.database.models import Player
import logging

logger = logging.getLogger(__name__)


class CardType(Enum):
    FAKE_TASK = "fake_task"
    DOUBLE_VOTE = "double_vote"
    ANONYMOUS_VOTE = "anonymous_vote"
    REVEAL_ROLE = "reveal_role"
    SABOTAGE_VOTE = "sabotage_vote"
    IMMUNITY = "immunity"
    WHISPER = "whisper"
    DECOY = "decoy"


class BetrayalCard:
    """Represents a betrayal card with special abilities."""

    def __init__(
        self,
        card_type: CardType,
        name: str,
        description: str,
        rarity: str,
        effect: Dict,
        usage_limit: int = 1,
    ):
        self.card_type = card_type
        self.name = name
        self.description = description
        self.rarity = rarity  # common, rare, epic, legendary
        self.effect = effect
        self.usage_limit = usage_limit
        self.emoji = self._get_card_emoji(card_type)

    def _get_card_emoji(self, card_type: CardType) -> str:
        """Get emoji for card type."""
        emojis = {
            CardType.FAKE_TASK: "🛠️",
            CardType.DOUBLE_VOTE: "🗳️",
            CardType.ANONYMOUS_VOTE: "👤",
            CardType.REVEAL_ROLE: "🔍",
            CardType.SABOTAGE_VOTE: "💣",
            CardType.IMMUNITY: "🛡️",
            CardType.WHISPER: "💬",
            CardType.DECOY: "🎭",
        }
        return emojis.get(card_type, "🃏")


class BetrayalCardsSystem:
    """Manages betrayal cards and emergent gameplay mechanics."""

    def __init__(self):
        # Define all betrayal cards
        self.card_definitions = {
            CardType.FAKE_TASK: BetrayalCard(
                CardType.FAKE_TASK,
                "Fake Task",
                "Complete a fake task to earn XP",
                "common",
                {"xp_gain": 5, "fake_task": True},
                1,
            ),
            CardType.DOUBLE_VOTE: BetrayalCard(
                CardType.DOUBLE_VOTE,
                "Double Vote",
                "Your vote counts twice this round",
                "rare",
                {"vote_multiplier": 2},
                1,
            ),
            CardType.ANONYMOUS_VOTE: BetrayalCard(
                CardType.ANONYMOUS_VOTE,
                "Anonymous Vote",
                "Vote without revealing your choice",
                "epic",
                {"anonymous_vote": True},
                1,
            ),
            CardType.REVEAL_ROLE: BetrayalCard(
                CardType.REVEAL_ROLE,
                "Role Reveal",
                "Reveal another player's role",
                "legendary",
                {"reveal_role": True},
                1,
            ),
            CardType.SABOTAGE_VOTE: BetrayalCard(
                CardType.SABOTAGE_VOTE,
                "Vote Sabotage",
                "Cancel another player's vote",
                "epic",
                {"sabotage_vote": True},
                1,
            ),
            CardType.IMMUNITY: BetrayalCard(
                CardType.IMMUNITY,
                "Immunity",
                "Cannot be voted out this round",
                "legendary",
                {"immunity": True},
                1,
            ),
            CardType.WHISPER: BetrayalCard(
                CardType.WHISPER,
                "Whisper",
                "Send a secret message to another player",
                "rare",
                {"whisper": True},
                3,
            ),
            CardType.DECOY: BetrayalCard(
                CardType.DECOY,
                "Decoy",
                "Create a fake player to confuse others",
                "epic",
                {"decoy": True},
                1,
            ),
        }

        # Track player inventories: {player_id: {card_type: count}}
        self.player_inventories = {}

        # Track active card effects: {game_id: {player_id: [active_effects]}}
        self.active_effects = {}

        # Track card usage history
        self.usage_history = []

    def add_card_to_inventory(
        self, player_id: int, card_type: CardType, count: int = 1
    ) -> bool:
        """Add cards to a player's inventory."""
        if player_id not in self.player_inventories:
            self.player_inventories[player_id] = {}

        if card_type.value not in self.player_inventories[player_id]:
            self.player_inventories[player_id][card_type.value] = 0

        self.player_inventories[player_id][card_type.value] += count

        logger.info(f"Added {count} {card_type.value} cards to player {player_id}")
        return True

    def get_player_inventory(self, player_id: int) -> Dict[str, int]:
        """Get a player's card inventory."""
        return self.player_inventories.get(player_id, {})

    def use_card(
        self,
        player_id: int,
        card_type: CardType,
        game_id: str,
        target_player_id: Optional[int] = None,
    ) -> Tuple[bool, str]:
        """Use a betrayal card."""
        if player_id not in self.player_inventories:
            return False, "❌ No cards in inventory."

        if card_type.value not in self.player_inventories[player_id]:
            return False, f"❌ You don't have any {card_type.value} cards."

        if self.player_inventories[player_id][card_type.value] <= 0:
            return False, f"❌ You don't have any {card_type.value} cards."

        card = self.card_definitions[card_type]

        # Check if card can be used in current game state
        if not self._can_use_card(card, game_id, player_id):
            return False, f"❌ Cannot use {card.name} right now."

        # Use the card
        self.player_inventories[player_id][card_type.value] -= 1

        # Apply card effect
        effect_result = self._apply_card_effect(
            card, player_id, game_id, target_player_id
        )

        # Log usage
        self.usage_history.append(
            {
                "player_id": player_id,
                "card_type": card_type.value,
                "game_id": game_id,
                "target_player_id": target_player_id,
                "used_at": datetime.now(),
                "effect_result": effect_result,
            }
        )

        logger.info(f"Player {player_id} used {card_type.value} card in game {game_id}")

        return True, (
            f"🃏 **{card.name} Used!**\n\n"
            f"📝 {card.description}\n"
            f"✨ Effect: {effect_result}"
        )

    def _can_use_card(self, card: BetrayalCard, game_id: str, player_id: int) -> bool:
        """Check if a card can be used in the current game state."""
        # This would need to be integrated with the game state
        # For now, return True for most cards
        return True

    def _apply_card_effect(
        self,
        card: BetrayalCard,
        player_id: int,
        game_id: str,
        target_player_id: Optional[int] = None,
    ) -> str:
        """Apply a card's effect and return description."""
        effect = card.effect

        if card.card_type == CardType.FAKE_TASK:
            # Add XP for fake task
            db = SessionLocal()
            try:
                player = db.query(Player).filter(Player.id == player_id).first()
                if player:
                    xp_gain = effect.get("xp_gain", 5)
                    player.xp += xp_gain
                    db.commit()
                    return f"Gained {xp_gain} XP from fake task"
            finally:
                db.close()

        elif card.card_type == CardType.DOUBLE_VOTE:
            # Set up double vote effect
            if game_id not in self.active_effects:
                self.active_effects[game_id] = {}
            if player_id not in self.active_effects[game_id]:
                self.active_effects[game_id][player_id] = []

            self.active_effects[game_id][player_id].append(
                {
                    "type": "double_vote",
                    "multiplier": effect.get("vote_multiplier", 2),
                    "expires_after": "next_vote",
                }
            )
            return "Your next vote will count twice"

        elif card.card_type == CardType.ANONYMOUS_VOTE:
            # Set up anonymous vote effect
            if game_id not in self.active_effects:
                self.active_effects[game_id] = {}
            if player_id not in self.active_effects[game_id]:
                self.active_effects[game_id][player_id] = []

            self.active_effects[game_id][player_id].append(
                {"type": "anonymous_vote", "expires_after": "next_vote"}
            )
            return "Your next vote will be anonymous"

        elif card.card_type == CardType.IMMUNITY:
            # Set up immunity effect
            if game_id not in self.active_effects:
                self.active_effects[game_id] = {}
            if player_id not in self.active_effects[game_id]:
                self.active_effects[game_id][player_id] = []

            self.active_effects[game_id][player_id].append(
                {"type": "immunity", "expires_after": "next_vote"}
            )
            return "You are immune to the next vote"

        elif card.card_type == CardType.WHISPER:
            if target_player_id:
                return f"Sent a secret whisper to player {target_player_id}"
            else:
                return "Whisper ability activated"

        elif card.card_type == CardType.DECOY:
            return "Created a decoy to confuse other players"

        return f"Applied {card.name} effect"

    def get_active_effects(self, game_id: str, player_id: int) -> List[Dict]:
        """Get active effects for a player in a game."""
        if game_id not in self.active_effects:
            return []

        return self.active_effects[game_id].get(player_id, [])

    def clear_expired_effects(self, game_id: str, event_type: str):
        """Clear effects that expire after a specific event."""
        if game_id not in self.active_effects:
            return

        for player_id in list(self.active_effects[game_id].keys()):
            effects = self.active_effects[game_id][player_id]
            remaining_effects = []

            for effect in effects:
                if effect.get("expires_after") != event_type:
                    remaining_effects.append(effect)

            if remaining_effects:
                self.active_effects[game_id][player_id] = remaining_effects
            else:
                del self.active_effects[game_id][player_id]

    def generate_inventory_display(self, player_id: int) -> str:
        """Generate a display of player's card inventory."""
        inventory = self.get_player_inventory(player_id)

        if not inventory:
            return "🃏 **No Betrayal Cards**\n\nEarn cards by opening crates or completing missions!"

        display = "🃏 **Your Betrayal Cards**\n\n"

        for card_type_value, count in inventory.items():
            if count > 0:
                card_type = CardType(card_type_value)
                card = self.card_definitions[card_type]

                display += (
                    f"{card.emoji} **{card.name}** x{count}\n"
                    f"📝 {card.description}\n"
                    f"⭐ {card.rarity.title()}\n\n"
                )

        return display

    def get_card_info(self, card_type: CardType) -> Optional[Dict]:
        """Get information about a specific card."""
        if card_type not in self.card_definitions:
            return None

        card = self.card_definitions[card_type]

        return {
            "name": card.name,
            "description": card.description,
            "rarity": card.rarity,
            "effect": card.effect,
            "usage_limit": card.usage_limit,
            "emoji": card.emoji,
        }

    def get_rare_cards(self) -> List[BetrayalCard]:
        """Get all rare and above cards."""
        rare_cards = []
        for card in self.card_definitions.values():
            if card.rarity in ["rare", "epic", "legendary"]:
                rare_cards.append(card)
        return rare_cards

    def get_card_usage_stats(self, player_id: int) -> Dict:
        """Get card usage statistics for a player."""
        player_usage = [u for u in self.usage_history if u["player_id"] == player_id]

        stats = {
            "total_cards_used": len(player_usage),
            "cards_by_type": {},
            "most_used_card": None,
            "recent_usage": [],
        }

        # Count by card type
        for usage in player_usage:
            card_type = usage["card_type"]
            if card_type not in stats["cards_by_type"]:
                stats["cards_by_type"][card_type] = 0
            stats["cards_by_type"][card_type] += 1

        # Find most used card
        if stats["cards_by_type"]:
            stats["most_used_card"] = max(
                stats["cards_by_type"].items(), key=lambda x: x[1]
            )[0]

        # Recent usage (last 10)
        stats["recent_usage"] = player_usage[-10:] if player_usage else []

        return stats


# Global instance
betrayal_cards_system = BetrayalCardsSystem()
