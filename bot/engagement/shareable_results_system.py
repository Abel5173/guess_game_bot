"""
Shareable Results System - Social proof and viral sharing mechanics.
"""

import random
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from bot.database import SessionLocal
from bot.database.models import Player
import logging

logger = logging.getLogger(__name__)


class ShareableResult:
    """Represents a shareable game result."""

    def __init__(self, player_id: int, game_id: str, result_data: Dict):
        self.player_id = player_id
        self.game_id = game_id
        self.result_data = result_data
        self.created_at = datetime.now()
        self.share_count = 0
        self.reactions = {}  # emoji: count

    def to_dict(self):
        return {
            "player_id": self.player_id,
            "game_id": self.game_id,
            "result_data": self.result_data,
            "created_at": self.created_at.isoformat(),
            "share_count": self.share_count,
            "reactions": self.reactions,
        }


class ShareableResultsSystem:
    """Manages shareable results and social sharing mechanics."""

    def __init__(self):
        # Store shareable results: {result_id: ShareableResult}
        self.shareable_results = {}

        # Track sharing statistics
        self.sharing_stats = {}

        # Viral sharing templates
        self.sharing_templates = {
            "crewmate_win": [
                "I just survived as a Crewmate! 🎉",
                "Crewmates win again! I helped solve the mystery 🔍",
                "Another victory for the good guys! ✨",
                "Impostor caught! Justice served! ⚖️",
            ],
            "impostor_win": [
                "I just won as the Impostor! 😈",
                "Deception successful! They never saw it coming 🎭",
                "Impostor victory! The perfect crime 💀",
                "They trusted me... their mistake! 😏",
            ],
            "mvp_performance": [
                "MVP performance! I carried the team! 🏆",
                "Best player award! I'm on fire! 🔥",
                "Unstoppable! MVP in another game! ⭐",
                "They call me the game master! 👑",
            ],
            "close_game": [
                "That was intense! Down to the wire! 😰",
                "Heart-pounding finish! What a game! 💓",
                "Closest game ever! Edge of my seat! 🎢",
                "Unbelievable ending! Still shaking! 🤯",
            ],
            "first_win": [
                "First victory! I'm getting the hang of this! 🎯",
                "Finally won! The learning curve is real! 📈",
                "First win achieved! Many more to come! 🚀",
                "Victory at last! I'm hooked! 🎮",
            ],
        }

        # Achievement badges for sharing
        self.sharing_badges = {
            "first_share": "📤 First Share",
            "viral_share": "🔥 Viral Share",
            "consistent_sharer": "📊 Consistent Sharer",
            "reaction_master": "💬 Reaction Master",
        }

    def create_shareable_result(
        self, player_id: int, game_id: str, game_result: Dict
    ) -> str:
        """Create a shareable result for a game."""
        result_id = f"{player_id}_{game_id}_{int(datetime.now().timestamp())}"

        # Determine result type for template selection
        result_type = self._determine_result_type(game_result)

        # Get player info
        db = SessionLocal()
        try:
            player = db.query(Player).filter(Player.id == player_id).first()
            if not player:
                return "❌ Player not found."

            # Create shareable result
            shareable_result = ShareableResult(player_id, game_id, game_result)
            self.shareable_results[result_id] = shareable_result

            # Generate shareable message
            share_message = self._generate_share_message(
                player, game_result, result_type, result_id
            )

            logger.info(f"Created shareable result {result_id} for player {player_id}")

            return share_message

        finally:
            db.close()

    def _determine_result_type(self, game_result: Dict) -> str:
        """Determine the type of result for template selection."""
        won = game_result.get("won", False)
        role = game_result.get("role", "crewmate")
        mvp = game_result.get("mvp", False)
        close_game = game_result.get("close_game", False)
        first_win = game_result.get("first_win", False)

        if first_win:
            return "first_win"
        elif mvp:
            return "mvp_performance"
        elif close_game:
            return "close_game"
        elif won and role == "crewmate":
            return "crewmate_win"
        elif won and role == "impostor":
            return "impostor_win"
        else:
            return "crewmate_win"  # Default

    def _generate_share_message(
        self, player: Player, game_result: Dict, result_type: str, result_id: str
    ) -> str:
        """Generate a shareable message."""
        # Select random template
        templates = self.sharing_templates.get(
            result_type, self.sharing_templates["crewmate_win"]
        )
        template = random.choice(templates)

        # Game statistics
        players_count = game_result.get("players_count", 0)
        tasks_completed = game_result.get("tasks_completed", 0)
        xp_gained = game_result.get("xp_gained", 0)
        role = game_result.get("role", "crewmate")
        won = game_result.get("won", False)

        # Role emoji
        role_emoji = "👨‍🚀" if role == "crewmate" else "🎭"
        outcome_emoji = "✅" if won else "❌"

        # Generate the message
        message = (
            f"{template}\n\n"
            f"🎮 **Game #{game_result.get('game_id', 'Unknown')}**\n"
            f"{role_emoji} **Role:** {role.title()}\n"
            f"{outcome_emoji} **Result:** {'Victory' if won else 'Defeat'}\n"
            f"👥 **Players:** {players_count}\n"
            f"🔧 **Tasks:** {tasks_completed}\n"
            f"✨ **XP:** +{xp_gained}\n"
            f"🏷️ **Title:** {player.title}\n\n"
            f"🎯 **Play with us:** @abel5173_bot\n"
            f"📤 **Share ID:** `{result_id}`"
        )

        return message

    def share_result(
        self, result_id: str, share_method: str = "telegram"
    ) -> Tuple[bool, str]:
        """Record a share of a result."""
        if result_id not in self.shareable_results:
            return False, "❌ Result not found."

        result = self.shareable_results[result_id]
        result.share_count += 1

        # Track sharing statistics
        if result.player_id not in self.sharing_stats:
            self.sharing_stats[result.player_id] = {
                "total_shares": 0,
                "shares_by_method": {},
                "viral_shares": 0,
            }

        self.sharing_stats[result.player_id]["total_shares"] += 1

        if share_method not in self.sharing_stats[result.player_id]["shares_by_method"]:
            self.sharing_stats[result.player_id]["shares_by_method"][share_method] = 0

        self.sharing_stats[result.player_id]["shares_by_method"][share_method] += 1

        # Check for viral share (10+ shares)
        if result.share_count >= 10:
            self.sharing_stats[result.player_id]["viral_shares"] += 1

        logger.info(f"Result {result_id} shared via {share_method}")

        return True, f"✅ Result shared! Total shares: {result.share_count}"

    def add_reaction(self, result_id: str, emoji: str) -> Tuple[bool, str]:
        """Add a reaction to a shared result."""
        if result_id not in self.shareable_results:
            return False, "❌ Result not found."

        result = self.shareable_results[result_id]

        if emoji not in result.reactions:
            result.reactions[emoji] = 0

        result.reactions[emoji] += 1

        logger.info(f"Added reaction {emoji} to result {result_id}")

        return True, f"✅ Reaction added! {emoji} count: {result.reactions[emoji]}"

    def get_viral_results(self, limit: int = 10) -> List[Dict]:
        """Get the most viral (shared) results."""
        viral_results = []

        for result_id, result in self.shareable_results.items():
            if result.share_count > 0:
                viral_results.append(
                    {
                        "result_id": result_id,
                        "player_id": result.player_id,
                        "share_count": result.share_count,
                        "created_at": result.created_at,
                        "reactions": result.reactions,
                    }
                )

        # Sort by share count
        viral_results.sort(key=lambda x: x["share_count"], reverse=True)

        return viral_results[:limit]

    def get_player_sharing_stats(self, player_id: int) -> Dict:
        """Get sharing statistics for a player."""
        if player_id not in self.sharing_stats:
            return {
                "total_shares": 0,
                "shares_by_method": {},
                "viral_shares": 0,
                "recent_results": [],
            }

        stats = self.sharing_stats[player_id].copy()

        # Get recent results
        recent_results = []
        for result_id, result in self.shareable_results.items():
            if result.player_id == player_id:
                recent_results.append(
                    {
                        "result_id": result_id,
                        "share_count": result.share_count,
                        "created_at": result.created_at,
                        "reactions": result.reactions,
                    }
                )

        # Sort by creation date
        recent_results.sort(key=lambda x: x["created_at"], reverse=True)
        stats["recent_results"] = recent_results[:5]  # Last 5 results

        return stats

    def generate_sharing_leaderboard(self) -> str:
        """Generate a leaderboard of top sharers."""
        # Get all players with sharing stats
        top_sharers = []

        for player_id, stats in self.sharing_stats.items():
            if stats["total_shares"] > 0:
                db = SessionLocal()
                try:
                    player = db.query(Player).filter(Player.id == player_id).first()
                    if player:
                        top_sharers.append(
                            {
                                "player_name": player.name,
                                "total_shares": stats["total_shares"],
                                "viral_shares": stats["viral_shares"],
                            }
                        )
                finally:
                    db.close()

        # Sort by total shares
        top_sharers.sort(key=lambda x: x["total_shares"], reverse=True)

        if not top_sharers:
            return "📤 **No sharing activity yet**\n\nShare your game results to appear here!"

        display = "📤 **Top Sharers**\n\n"

        for i, sharer in enumerate(top_sharers[:10], 1):
            crown = "👑" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
            viral_badge = "🔥" if sharer["viral_shares"] > 0 else ""

            display += (
                f"{crown} **{sharer['player_name']}**\n"
                f"   📤 {sharer['total_shares']} shares {viral_badge}\n\n"
            )

        return display

    def get_result_by_id(self, result_id: str) -> Optional[ShareableResult]:
        """Get a shareable result by ID."""
        return self.shareable_results.get(result_id)

    def generate_result_display(self, result_id: str) -> str:
        """Generate a display for a specific result."""
        result = self.get_result_by_id(result_id)
        if not result:
            return "❌ Result not found."

        db = SessionLocal()
        try:
            player = db.query(Player).filter(Player.id == result.player_id).first()
            if not player:
                return "❌ Player not found."

            game_result = result.result_data

            display = (
                f"📊 **Game Result**\n\n"
                f"👤 **Player:** {player.name}\n"
                f"🎮 **Game:** #{game_result.get('game_id', 'Unknown')}\n"
                f"📅 **Date:** {result.created_at.strftime('%Y-%m-%d %H:%M')}\n\n"
                f"📈 **Statistics:**\n"
                f"• Role: {game_result.get('role', 'Unknown')}\n"
                f"• Result: {'Victory' if game_result.get('won') else 'Defeat'}\n"
                f"• Players: {game_result.get('players_count', 0)}\n"
                f"• Tasks: {game_result.get('tasks_completed', 0)}\n"
                f"• XP: +{game_result.get('xp_gained', 0)}\n\n"
                f"📤 **Shares:** {result.share_count}\n"
            )

            if result.reactions:
                display += "💬 **Reactions:**\n"
                for emoji, count in result.reactions.items():
                    display += f"• {emoji}: {count}\n"

            return display

        finally:
            db.close()

    def cleanup_old_results(self, days: int = 30):
        """Clean up old shareable results."""
        cutoff_date = datetime.now() - timedelta(days=days)
        old_results = []

        for result_id, result in self.shareable_results.items():
            if result.created_at < cutoff_date:
                old_results.append(result_id)

        for result_id in old_results:
            del self.shareable_results[result_id]

        if old_results:
            logger.info(f"Cleaned up {len(old_results)} old shareable results")


# Global instance
shareable_results_system = ShareableResultsSystem()
