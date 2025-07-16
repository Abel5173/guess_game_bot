"""
Handlers for topic-based game functionality.
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import ContextTypes
from bot.topic_manager import topic_handler
import logging

logger = logging.getLogger(__name__)


async def create_topic_game_handler(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Handler for creating a new topic-based game."""
    await topic_handler.create_game_topic(update, context)


async def join_topic_game_handler(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Handler for joining a topic-based game."""
    query = update.callback_query
    if not query:
        return

    # Extract topic_id from callback data
    try:
        topic_id = int(query.data.split("_")[2])
        await topic_handler.join_topic_game(update, context, topic_id)
    except (IndexError, ValueError):
        await query.answer("❌ Invalid game session!")


async def start_topic_game_handler(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Handler for starting a topic-based game."""
    query = update.callback_query
    if not query:
        return

    # Extract topic_id from callback data
    try:
        topic_id = int(query.data.split("_")[2])
        await topic_handler.start_topic_game(update, context, topic_id)
    except (IndexError, ValueError):
        await query.answer("❌ Invalid game session!")


async def join_queue_handler(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Handler for joining the global game queue."""
    query = update.callback_query
    if not query:
        return
    user_id = query.from_user.id
    if topic_handler.topic_manager.add_to_queue(user_id):
        await query.answer(
            "✅ You have joined the queue! You'll be notified when a game is available."
        )
    else:
        await query.answer("⚠️ You are already in the queue.")


async def show_available_games_handler(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Handler for showing available games."""
    chat = update.effective_chat
    if not chat.is_forum:
        await update.message.reply_text(
            "❌ This feature requires a forum/supergroup with topics enabled."
        )
        return
    available_topics = topic_handler.topic_manager.get_available_topics(chat.id)
    if not available_topics:
        # No available games, offer to create one or join queue
        keyboard = [
            [
                InlineKeyboardButton(
                    "🎮 Create New Game", callback_data="create_topic_game"
                )
            ],
            [InlineKeyboardButton("⏳ Join Queue", callback_data="join_queue")],
        ]
        await update.message.reply_text(
            "🎮 **No active games available**\n\nWould you like to create a new game room or join the queue?",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
        return
    # Check if all games are full
    all_full = all(
        metadata["player_count"] >= metadata["max_players"]
        for _, metadata in available_topics
    )
    keyboard_buttons = []
    text = "🎮 **Available Games**\n\n"
    for topic_id, metadata in available_topics:
        text += (
            f"🎯 **{metadata['name']}**\n"
            f"👥 Players: {metadata['player_count']}/{metadata['max_players']}\n"
            f"⏰ Created: {metadata['created_at'].strftime('%H:%M')}\n\n"
        )
        keyboard_buttons.append(
            [
                InlineKeyboardButton(
                    f"Join {metadata['name']}", callback_data=f"join_topic_{topic_id}"
                )
            ]
        )
    keyboard_buttons.append(
        [InlineKeyboardButton("🎮 Create New Game", callback_data="create_topic_game")]
    )
    if all_full:
        keyboard_buttons.append(
            [InlineKeyboardButton("⏳ Join Queue", callback_data="join_queue")]
        )
    keyboard = InlineKeyboardMarkup(keyboard_buttons)
    await update.message.reply_text(
        text, parse_mode=ParseMode.MARKDOWN, reply_markup=keyboard
    )


async def topic_message_handler(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Handler for routing messages in topics to the correct game session."""
    await topic_handler.handle_topic_message(update, context)


async def rules_topic_handler(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Handler for showing rules in a topic."""
    query = update.callback_query
    if not query:
        return

    try:
        topic_id = int(query.data.split("_")[2])
        game = topic_handler.topic_manager.get_game_session(topic_id)

        if not game:
            await query.answer("❌ Game session not found!")
            return

        rules_text = (
            "📋 **Game Rules**\n\n"
            "🎭 **Objective:**\n"
            "• Crewmates: Complete tasks and identify the impostor\n"
            "• Impostor: Eliminate crewmates without being caught\n\n"
            "🎯 **How to Play:**\n"
            "1. **Task Phase:** Complete assigned tasks\n"
            "2. **Discussion:** Discuss suspicions and share clues\n"
            "3. **Voting:** Vote to eject a player\n"
            "4. **Repeat** until impostor is caught or wins\n\n"
            "💡 **Tips:**\n"
            "• Pay attention to player behavior\n"
            "• Use the AI-generated clues wisely\n"
            "• Work together as crewmates\n"
            "• Blend in as the impostor\n\n"
            "🎮 **Commands:**\n"
            "• /task - Get your current task\n"
            "• /answer <answer> - Submit task answer\n"
            "• /status - Check game status"
        )

        await query.message.reply_text(rules_text, parse_mode="Markdown")
        await query.answer()

    except (IndexError, ValueError):
        await query.answer("❌ Invalid game session!")


async def close_topic_handler(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Handler for closing a topic."""
    query = update.callback_query
    if not query:
        return

    try:
        topic_id = int(query.data.split("_")[2])
        metadata = topic_handler.topic_manager.topic_metadata.get(topic_id)

        if not metadata:
            await query.answer("❌ Topic not found!")
            return

        # Check if user is the creator
        if query.from_user.id != metadata["creator_id"]:
            await query.answer("❌ Only the creator can close the topic!")
            return

        # Remove the game session
        topic_handler.topic_manager.remove_game_session(topic_id)

        # Close the topic (this would require bot admin rights)
        try:
            await context.bot.close_forum_topic(
                chat_id=query.message.chat.id, message_thread_id=topic_id
            )
            await query.answer("✅ Topic closed!")
        except Exception as e:
            logger.error(f"Failed to close topic: {e}")
            await query.answer("⚠️ Topic session removed, but couldn't close topic")

    except (IndexError, ValueError):
        await query.answer("❌ Invalid topic!")


async def leaderboard_topic_handler(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Handler for showing leaderboard in a topic."""
    query = update.callback_query
    if not query:
        return
    try:
        topic_id = int(query.data.split("_")[2])
        game = topic_handler.topic_manager.get_game_session(topic_id)
        if not game:
            await query.answer("❌ Game session not found!")
            return
        # Build leaderboard for this topic
        players = game.core.players
        if not players:
            await query.message.reply_text("No players in this game yet.")
            await query.answer()
            return
        # Sort by XP if available, else by join order
        leaderboard = sorted(
            players.items(), key=lambda x: x[1].get("xp", 0), reverse=True
        )
        lines = ["🏆 <b>Game Room Leaderboard</b>"]
        for i, (uid, pdata) in enumerate(leaderboard, 1):
            name = pdata.get("name", f"Player {uid}")
            xp = pdata.get("xp", 0)
            lines.append(f"{i}. {name} — {xp} XP")
        await query.message.reply_text("\n".join(lines), parse_mode="HTML")
        await query.answer()
    except (IndexError, ValueError):
        await query.answer("❌ Invalid game session!")


async def callback_query_handler(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Main callback query handler for topic-related actions."""
    query = update.callback_query
    if not query:
        return

    callback_data = query.data

    try:
        if callback_data == "create_topic_game":
            await create_topic_game_handler(update, context)
        elif callback_data == "join_queue":
            await join_queue_handler(update, context)
        elif callback_data.startswith("join_topic_"):
            await join_topic_game_handler(update, context)
        elif callback_data.startswith("start_topic_"):
            await start_topic_game_handler(update, context)
        elif callback_data.startswith("rules_topic_"):
            await rules_topic_handler(update, context)
        elif callback_data.startswith("close_topic_"):
            await close_topic_handler(update, context)
        elif callback_data.startswith("leaderboard_topic_"):
            await leaderboard_topic_handler(update, context)
        else:
            # Let other handlers deal with it
            return False

        return True

    except Exception as e:
        logger.error(f"Error in topic callback handler: {e}")
        await query.answer("❌ An error occurred!")
        return True
