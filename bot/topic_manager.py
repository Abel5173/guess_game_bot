"""
Topic Manager for handling concurrent game sessions using Telegram Topics.
"""

import asyncio
from typing import Dict, Optional, List, Tuple
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
from bot.impostor import ImpostorGame
from bot.database import SessionLocal
from bot.database.models import GameSession, Player
from bot.database.session_manager import GameSessionManager, JoinQueueManager
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class TopicManager:
    """
    Manages game sessions using Telegram Topics for concurrent gameplay.
    Each topic represents a separate game room.
    """

    def __init__(self):
        logger.debug("Initializing TopicManager")
        # Store active game sessions: {topic_id: ImpostorGame}
        self.active_sessions: Dict[int, ImpostorGame] = {}
        # Store topic metadata: {topic_id: TopicMetadata}
        self.topic_metadata: Dict[int, dict] = {}
        # Store join requests: {topic_id: List[user_id]}
        self.join_requests: Dict[int, List[int]] = {}
        # Database managers
        self.session_manager = GameSessionManager()
        self.queue_manager = JoinQueueManager()

    def get_game_session(self, topic_id: int) -> Optional[ImpostorGame]:
        logger.info(f"get_game_session called with topic_id={topic_id}")
        """Get the game session for a specific topic."""
        return self.active_sessions.get(topic_id)

    def create_game_session(
        self, topic_id: int, topic_name: str, creator_id: int, chat_id: int
    ) -> ImpostorGame:
        """Create a new game session for a topic."""
        game = ImpostorGame()
        self.active_sessions[topic_id] = game

        # Create database session
        db_session = self.session_manager.create_session(
            topic_id=topic_id,
            chat_id=chat_id,
            creator_id=creator_id,
            topic_name=topic_name,
        )

        # Set the database session ID in the game
        game.set_db_session_id(db_session.id)

        self.topic_metadata[topic_id] = {
            "name": topic_name,
            "creator_id": creator_id,
            "created_at": datetime.now(),
            "status": "waiting",  # waiting, active, finished
            "player_count": 0,
            "max_players": 10,
            "db_session_id": db_session.id,
        }
        self.join_requests[topic_id] = []
        logger.info(f"Created game session for topic {topic_id}: {topic_name}")
        return game

    def remove_game_session(self, topic_id: int):
        """Remove a game session and clean up."""
        if topic_id in self.active_sessions:
            del self.active_sessions[topic_id]
        if topic_id in self.topic_metadata:
            del self.topic_metadata[topic_id]
        if topic_id in self.join_requests:
            del self.join_requests[topic_id]
        logger.info(f"Removed game session for topic {topic_id}")

    def get_available_topics(self, chat_id: int) -> List[Tuple[int, dict]]:
        """Get list of available topics for joining."""
        available = []
        for topic_id, metadata in self.topic_metadata.items():
            if (
                metadata["status"] == "waiting"
                and metadata["player_count"] < metadata["max_players"]
            ):
                available.append((topic_id, metadata))
        return available

    def cleanup_old_sessions(self, max_age_hours: int = 24):
        """Clean up old game sessions."""
        # Clean up in-memory sessions
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
        to_remove = []

        for topic_id, metadata in self.topic_metadata.items():
            if metadata["created_at"] < cutoff_time:
                to_remove.append(topic_id)

        for topic_id in to_remove:
            self.remove_game_session(topic_id)

        # Clean up database sessions
        self.session_manager.cleanup_old_sessions(max_age_hours)

        if to_remove:
            logger.info(f"Cleaned up {len(to_remove)} old game sessions")

    def add_to_queue(self, user_id: int, chat_id: int) -> bool:
        """Add user to join queue in database."""
        return self.queue_manager.add_to_queue(user_id, chat_id)

    def remove_from_queue(self, user_id: int) -> bool:
        """Remove user from join queue in database."""
        with self.queue_manager as qm:
            return qm.remove_from_queue(user_id)

    def get_queue(self, chat_id: Optional[int] = None) -> List[int]:
        """Get users in join queue from database."""
        queue_entries = self.queue_manager.get_queue(chat_id)
        return [entry.player_id for entry in queue_entries]

    def recover_active_sessions(self):
        """Recover active sessions from database on bot restart."""
        active_sessions = self.session_manager.get_active_sessions()

        for db_session in active_sessions:
            try:
                # Create game instance
                game = ImpostorGame()
                game.set_db_session_id(db_session.id)

                # Add to active sessions
                self.active_sessions[db_session.topic_id] = game

                # Recreate metadata
                self.topic_metadata[db_session.topic_id] = {
                    "name": db_session.topic_name,
                    "creator_id": db_session.creator_id,
                    "created_at": db_session.created_at,
                    "status": db_session.status,
                    "player_count": 0,  # Will be updated when players join
                    "max_players": db_session.max_players,
                    "db_session_id": db_session.id,
                    "chat_id": db_session.chat_id,
                }

                # Recover players
                player_links = self.session_manager.get_session_players(db_session.id)
                for player_link in player_links:
                    if player_link.left_at is None:  # Only active players
                        game.add_player(player_link.player_id, player_link.player.name)
                        self.topic_metadata[db_session.topic_id]["player_count"] += 1

                logger.info(
                    f"Recovered session {db_session.id} for topic {db_session.topic_id}"
                )

            except Exception as e:
                logger.error(f"Failed to recover session {db_session.id}: {e}")

        logger.info(f"Recovered {len(active_sessions)} active sessions from database")


class TopicGameHandler:
    """
    Handles game logic specific to topic-based gameplay.
    """

    def __init__(self):
        self.topic_manager = TopicManager()

    async def notify_queue(
        self, context: ContextTypes.DEFAULT_TYPE, topic_id: int, metadata: dict
    ):
        """Notify users in the join queue that a game is available."""
        chat_id = metadata.get("chat_id")
        if not chat_id:
            return

        # Get queued users from database
        queued_users = self.topic_manager.get_queue(chat_id)
        notified = []

        for user_id in queued_users:
            try:
                await context.bot.send_message(
                    chat_id=user_id,
                    text=(
                        f"🎮 A new game room is available: <b>{metadata['name']}</b>!\n"
                        f"Click the group and join the topic to play!"
                    ),
                    parse_mode="HTML",
                )
                notified.append(user_id)
            except Exception:
                pass

        # Mark users as notified in database
        if notified:
            self.topic_manager.queue_manager.notify_queue(chat_id)

    async def create_game_topic(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> Optional[int]:
        """
        Create a new topic for a game session.
        Returns the topic_id if successful, None otherwise.
        """
        chat = update.effective_chat
        user = update.effective_user

        if not chat.is_forum:
            await update.message.reply_text(
                "❌ This feature requires a forum/supergroup with topics enabled."
            )
            return None

        # Generate topic name
        topic_count = len(self.topic_manager.active_sessions) + 1
        topic_name = f"🎮 Game #{topic_count} - Join to Play!"

        try:
            # Create the topic
            result = await context.bot.create_forum_topic(
                chat_id=chat.id,
                name=topic_name,
                icon_color=0x6FB9F0,  # Blue color
                icon_custom_emoji_id=None,
            )

            topic_id = result.message_thread_id

            # Create game session (both in-memory and database)
            game = self.topic_manager.create_game_session(
                topic_id, topic_name, user.id, chat.id
            )

            # Send welcome message in the new topic
            welcome_text = (
                f"🎉 **Welcome to {topic_name}**\n\n"
                f"👤 **Game Creator:** {user.first_name}\n"
                f"⏰ **Created:** {datetime.now().strftime('%H:%M')}\n"
                f"👥 **Players:** 0/10\n\n"
                f"🎯 **How to join:**\n"
                "• Click 'Join Game' below\n"
                "• Wait for the creator to start\n"
                "• Have fun playing! 🎮"
            )

            join_keyboard = InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "🎮 Join Game", callback_data=f"join_topic_{topic_id}"
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            "📋 Rules", callback_data=f"rules_topic_{topic_id}"
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            "🏆 Leaderboard",
                            callback_data=f"leaderboard_topic_{topic_id}",
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            "❌ Close Topic", callback_data=f"close_topic_{topic_id}"
                        )
                    ],
                ]
            )

            await context.bot.send_message(
                chat_id=chat.id,
                message_thread_id=topic_id,
                text=welcome_text,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=join_keyboard,
            )

            # Update the main group
            await update.message.reply_text(
                f"✅ Created new game room: **{topic_name}**\n"
                f"Click the topic to join the game! 🎮",
                parse_mode=ParseMode.MARKDOWN,
            )

            # Notify queued users
            await self.notify_queue(
                context, topic_id, self.topic_manager.topic_metadata[topic_id]
            )
            return topic_id

        except Exception as e:
            logger.error(f"Failed to create topic: {e}")
            await update.message.reply_text(
                "❌ Failed to create game topic. Please try again."
            )
            return None

    async def join_topic_game(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE, topic_id: int
    ):
        """Handle joining a topic-based game."""
        user = update.effective_user
        game = self.topic_manager.get_game_session(topic_id)

        if not game:
            await update.callback_query.answer("❌ Game session not found!")
            return

        metadata = self.topic_manager.topic_metadata.get(topic_id)
        if not metadata:
            await update.callback_query.answer("❌ Topic metadata not found!")
            return

        # Check if user is already in the game
        if user.id in game.core.players:
            await update.callback_query.answer("⚠️ You're already in this game!")
            return

        # Check if game is full
        if metadata["player_count"] >= metadata["max_players"]:
            await update.callback_query.answer("❌ Game is full!")
            return

        # Add player to game (both in-memory and database)
        if game.add_player(user.id, user.first_name):
            metadata["player_count"] += 1

            # Add to database
            db_session_id = metadata.get("db_session_id")
            if db_session_id:
                self.topic_manager.session_manager.add_player_to_session(
                    db_session_id, user.id
                )

            # Update the topic message
            await self._update_topic_status(context, topic_id, game, metadata)

            await update.callback_query.answer(f"✅ {user.first_name} joined the game!")

            # Send welcome message to the player
            try:
                await context.bot.send_message(
                    chat_id=user.id,
                    text=f"🎮 Welcome to {metadata['name']}! The game will start soon.",
                )
            except Exception:
                pass  # User might have blocked the bot

            # If a slot is now open, notify the queue
            if metadata["player_count"] < metadata["max_players"]:
                await self.notify_queue(context, topic_id, metadata)
        else:
            await update.callback_query.answer("⚠️ Failed to join game!")

    async def start_topic_game(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE, topic_id: int
    ):
        """Start a topic-based game."""
        user = update.effective_user
        game = self.topic_manager.get_game_session(topic_id)

        if not game:
            await update.callback_query.answer("❌ Game session not found!")
            return

        metadata = self.topic_manager.topic_metadata.get(topic_id)
        if not metadata:
            await update.callback_query.answer("❌ Topic metadata not found!")
            return

        # Check if user is the creator
        if user.id != metadata["creator_id"]:
            await update.callback_query.answer(
                "❌ Only the game creator can start the game!"
            )
            return

        # Check minimum players
        if len(game.core.players) < 4:
            await update.callback_query.answer("❌ Need at least 4 players to start!")
            return

        # Start the game
        game.core.group_chat_id = update.effective_chat.id
        if not game.core.start_game():
            await update.callback_query.answer("❌ Failed to start game!")
            return

        metadata["status"] = "active"

        # Update database status
        self.topic_manager.session_manager.update_session_status(topic_id, "active")

        # Notify all players
        for uid, player_data in game.core.players.items():
            try:
                await context.bot.send_message(
                    uid,
                    "🎭 The game has started! Check the topic for updates.",
                    parse_mode="HTML",
                )
            except Exception:
                pass

        # Start the task phase
        await game.phases.start_task_phase(context, topic_id)

        await update.callback_query.answer("🎮 Game started!")

    async def _update_topic_status(
        self,
        context: ContextTypes.DEFAULT_TYPE,
        topic_id: int,
        game: ImpostorGame,
        metadata: dict,
    ):
        """Update the status message in a topic (dynamic topic name)."""
        try:
            chat_id = None
            # Try to get chat_id from context if possible
            if hasattr(context, "chat_data") and context.chat_data:
                chat_id = list(context.chat_data.keys())[0]
            if (
                not chat_id
                and hasattr(context, "bot")
                and hasattr(context.bot, "chat_id")
            ):
                chat_id = context.bot.chat_id
            # Fallback: get from metadata if stored
            if not chat_id and "chat_id" in metadata:
                chat_id = metadata["chat_id"]
            # If not found, skip
            if not chat_id:
                return
            player_count = metadata["player_count"]
            max_players = metadata["max_players"]
            status = metadata["status"]
            base_name = metadata["name"].split("—")[0].strip()
            if status == "active":
                new_name = f"{base_name} — {player_count}/{max_players} Playing"
            else:
                new_name = f"{base_name} — {player_count}/{max_players} Waiting"
            # Update the topic name
            await context.bot.edit_forum_topic(
                chat_id=chat_id, message_thread_id=topic_id, name=new_name
            )
            metadata["name"] = new_name
        except Exception as e:
            logger.error(f"Failed to update topic status: {e}")

    async def handle_topic_message(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Route messages to the correct game session based on topic."""
        if not update.message or not update.message.is_topic_message:
            return

        topic_id = update.message.message_thread_id
        game = self.topic_manager.get_game_session(topic_id)

        if not game:
            return

        # Route the message to the appropriate game handler
        if game.core.phase == "discussion":
            await game.handle_discussion(update, context)
        elif game.core.phase == "voting":
            await game.handle_vote(update, context)

    async def show_available_games(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Show available games that can be joined."""
        chat = update.effective_chat

        if not chat.is_forum:
            await update.message.reply_text(
                "❌ This feature requires a forum/supergroup with topics enabled."
            )
            return

        available_topics = self.topic_manager.get_available_topics(chat.id)

        if not available_topics:
            # No available games, offer to create one
            keyboard = InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "🎮 Create New Game", callback_data="create_topic_game"
                        )
                    ]
                ]
            )
            await update.message.reply_text(
                "🎮 **No active games available**\n\n"
                "Would you like to create a new game room?",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=keyboard,
            )
            return

        # Show available games
        text = "🎮 **Available Games**\n\n"
        keyboard_buttons = []

        for topic_id, metadata in available_topics:
            text += (
                f"🎯 **{metadata['name']}**\n"
                f"👥 Players: {metadata['player_count']}/{metadata['max_players']}\n"
                f"⏰ Created: {metadata['created_at'].strftime('%H:%M')}\n\n"
            )
            keyboard_buttons.append(
                [
                    InlineKeyboardButton(
                        f"Join {metadata['name']}",
                        callback_data=f"join_topic_{topic_id}",
                    )
                ]
            )

        keyboard_buttons.append(
            [
                InlineKeyboardButton(
                    "🎮 Create New Game", callback_data="create_topic_game"
                )
            ]
        )
        keyboard = InlineKeyboardMarkup(keyboard_buttons)

        await update.message.reply_text(
            text, parse_mode=ParseMode.MARKDOWN, reply_markup=keyboard
        )


# Global instance
topic_handler = TopicGameHandler()
