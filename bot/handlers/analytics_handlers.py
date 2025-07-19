"""
Analytics handlers for database-powered insights and statistics.
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
from bot.database.session_manager import get_player_stats, get_team_stats, get_leaderboard
from bot.database import get_session
from bot.database.models import Player, GameSession
from sqlalchemy import func, desc
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


async def show_player_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show comprehensive stats for the current player."""
    logger.info(f"show_player_stats called by user {update.effective_user.id}")
    user = update.effective_user

    with get_session() as session:
        stats = get_player_stats(session, user.id)

    if not stats:
        await update.message.reply_text(
            "❌ You haven't played any games yet. Join a game to see your stats!"
        )
        return

    player = stats["player"]
    win_rate = stats["win_rate"] * 100

    stats_text = (
        f"📊 **Player Statistics** — {player.name}\n\n"
        f"🏷️ **Title:** {player.title}\n"
        f"✨ **Total XP:** {player.xp}\n"
        f"🎮 **Games Played:** {stats['games_played']}\n"
        f"🏆 **Games Won:** {stats['games_won']}\n"
        f"📈 **Win Rate:** {win_rate:.1f}%\n"
        f"🔧 **Tasks Completed:** {player.tasks_done}\n"
        f"🛠️ **Fake Tasks:** {player.fake_tasks_done}\n"
        f"💀 **Losses:** {player.losses}\n\n"
        f"🎯 **Performance:**\n"
        f"• Average XP per game: {player.xp / stats['games_played']:.1f}\n"
        f"• Task efficiency: {player.tasks_done / stats['games_played']:.1f} tasks/game"
    )

    await update.message.reply_text(stats_text, parse_mode=ParseMode.MARKDOWN)


async def show_session_leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show leaderboard for a specific game session."""
    # Extract session ID from command or use current session
    args = context.args
    if not args:
        await update.message.reply_text(
            "❌ Please specify a session ID: `/leaderboard <session_id>`",
            parse_mode=ParseMode.MARKDOWN,
        )
        return

    try:
        session_id = int(args[0])
    except ValueError:
        await update.message.reply_text(
            "❌ Invalid session ID. Please provide a number."
        )
        return

    with get_session() as session:
        leaderboard = get_leaderboard(session, session_id)

    if not leaderboard:
        await update.message.reply_text("❌ No data found for this session.")
        return

    leaderboard_text = f"🏆 **Session #{session_id} Leaderboard**\n\n"

    for entry in leaderboard:
        rank_emoji = (
            "🥇"
            if entry["rank"] == 1
            else (
                "🥈"
                if entry["rank"] == 2
                else "🥉" if entry["rank"] == 3 else f"{entry['rank']}."
            )
        )
        outcome_emoji = (
            "✅"
            if entry["outcome"] == "win"
            else "❌" if entry["outcome"] == "lose" else "🤷"
        )

        leaderboard_text += (
            f"{rank_emoji} **{entry['player_name']}**\n"
            f"   ✨ XP: {entry['xp_earned']} | "
            f"🎭 Role: {entry['role']} | "
            f"{outcome_emoji} {entry['outcome'] or 'N/A'}\n\n"
        )

    await update.message.reply_text(leaderboard_text, parse_mode=ParseMode.MARKDOWN)


async def show_chat_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show statistics for the current chat."""
    chat = update.effective_chat

    with get_session() as session:
        stats = get_team_stats(session, chat.id)

    completion_rate = stats["completion_rate"] * 100

    stats_text = (
        f"📊 **Chat Statistics** — {chat.title}\n\n"
        f"🎮 **Total Sessions:** {stats['total_sessions']}\n"
        f"⏳ **Active Sessions:** {stats['active_sessions']}\n"
        f"✅ **Completed Sessions:** {stats['finished_sessions']}\n"
        f"📈 **Completion Rate:** {completion_rate:.1f}%\n\n"
        f"📅 **Time Period:** Last 7 days"
    )

    await update.message.reply_text(stats_text, parse_mode=ParseMode.MARKDOWN)


async def show_global_leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show global leaderboard across all chats."""
    db = get_session()

    # Get top players by XP
    top_players = db.query(Player).order_by(desc(Player.xp)).limit(20).all()

    if not top_players:
        await update.message.reply_text("❌ No players found in the database.")
        db.close()
        return

    leaderboard_text = "🌍 **Global Leaderboard** — Top Players\n\n"

    for i, player in enumerate(top_players, 1):
        rank_emoji = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."

        leaderboard_text += (
            f"{rank_emoji} **{player.name}**\n"
            f"   ✨ {player.xp} XP | 🏷️ {player.title}\n"
            f"   🎮 {player.wins}W/{player.losses}L | "
            f"🔧 {player.tasks_done} tasks\n\n"
        )

    db.close()

    await update.message.reply_text(leaderboard_text, parse_mode=ParseMode.MARKDOWN)


async def show_recent_games(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show recent game sessions."""
    db = get_session()

    # Get recent sessions
    recent_sessions = (
        db.query(GameSession).order_by(desc(GameSession.created_at)).limit(10).all()
    )

    if not recent_sessions:
        await update.message.reply_text("❌ No recent games found.")
        db.close()
        return

    games_text = "🎮 **Recent Games**\n\n"

    for session in recent_sessions:
        status_emoji = {
            "waiting": "⏳",
            "active": "🎯",
            "finished": "✅",
            "abandoned": "❌",
        }.get(session.status, "❓")

        created_time = session.created_at.strftime("%m/%d %H:%M")

        games_text += (
            f"{status_emoji} **{session.topic_name}**\n"
            f"   📅 {created_time} | 🎭 {session.game_type}\n"
            f"   👥 {len(session.players)} players | "
            f"📊 {session.status}\n\n"
        )

    db.close()

    await update.message.reply_text(games_text, parse_mode=ParseMode.MARKDOWN)


async def show_analytics_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show analytics menu with available commands."""
    keyboard = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("📊 My Stats", callback_data="analytics_my_stats")],
            [
                InlineKeyboardButton(
                    "🏆 Global Leaderboard", callback_data="analytics_global_lb"
                )
            ],
            [
                InlineKeyboardButton(
                    "🎮 Recent Games", callback_data="analytics_recent_games"
                )
            ],
            [
                InlineKeyboardButton(
                    "📈 Chat Stats", callback_data="analytics_chat_stats"
                )
            ],
        ]
    )

    await update.message.reply_text(
        "📊 **Analytics Dashboard**\n\n" "Choose what you'd like to see:",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=keyboard,
    )


async def handle_analytics_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle analytics callback queries."""
    logger.info(f"handle_analytics_callback called by user {update.effective_user.id}")
    query = update.callback_query
    await query.answer()
    logger.debug(f"Analytics callback data: {query.data}")

    if query.data == "analytics_my_stats":
        # Create a mock update for the stats command
        mock_update = Update(0)
        mock_update.message = query.message
        mock_update.effective_user = query.from_user
        await show_player_stats(mock_update, context)

    elif query.data == "analytics_global_lb":
        mock_update = Update(0)
        mock_update.message = query.message
        mock_update.effective_user = query.from_user
        await show_global_leaderboard(mock_update, context)

    elif query.data == "analytics_recent_games":
        mock_update = Update(0)
        mock_update.message = query.message
        mock_update.effective_user = query.from_user
        await show_recent_games(mock_update, context)

    elif query.data == "analytics_chat_stats":
        mock_update = Update(0)
        mock_update.message = query.message
        mock_update.effective_user = query.from_user
        await show_chat_stats(mock_update, context)
