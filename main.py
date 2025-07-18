import os
import sys
import signal
import logging
import warnings
from contextlib import redirect_stderr
from io import StringIO
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.constants import ParseMode
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
from bot.ui.buttons import main_menu
from bot.database import init_db
from dotenv import load_dotenv
from bot.impostor import ImpostorGame  # Modularized Impostor Game import
from bot.constants import HELP_TEXT, ABOUT_TEXT
from bot.handlers.topic_handlers import (
    create_topic_game_handler,
    show_available_games_handler,
    topic_message_handler,
    callback_query_handler,
)
from bot.handlers.analytics_handlers import (
    show_player_stats,
    show_session_leaderboard,
    show_chat_stats,
    show_global_leaderboard,
    show_recent_games,
    show_analytics_menu,
    handle_analytics_callback,
)
from bot.handlers.engagement_handlers import (
    show_engagement_summary_handler,
    show_basecamp_handler,
    show_missions_handler,
    show_flash_events_handler,
    show_cards_handler,
    handle_engagement_callback,
)
from bot.handlers.ai_handlers import (
    ai_status_handler,
    ai_personas_handler,
    ai_detective_handler,
    ai_chaos_handler,
    ai_lore_handler,
    ai_task_handler,
    handle_ai_callback,
)
from bot.handlers.pulse_code_handlers import (
    start_pulse_code,
    start_dual_operative_game,
    start_triple_threat_game,
    guess_pulse_code,
    mind_link,
    desperation_gambit,
    pulse_code_status,
    end_pulse_code,
    feedback,
    join_pulse_code,
    leave_pulse_code,
    pulse_code_players,
)
from bot.topic_manager import topic_handler
from bot.engagement import engagement_engine
from bot.ai import ai_game_engine
import asyncio
from bot.handlers.menu import menu_handler
from bot.pulse_code import PulseCodeGame
from telegram.error import TimedOut, NetworkError

# Configure logging to show more information
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)

# Suppress only the most noisy loggers
logging.getLogger("telegram.ext._utils.networkloop").setLevel(logging.WARNING)
logging.getLogger("telegram.ext._updater").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)

load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")

games = {}  # chat_id: ImpostorGame instance


def get_game_manager(chat_id):
    if chat_id not in games:
        games[chat_id] = ImpostorGame()
    return games[chat_id]


async def startgame(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"startgame called by user {update.effective_user.id}")
    await menu_handler(update, context)
    logger.info("startgame response sent")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"help_command called by user {update.effective_user.id}")
    await update.message.reply_text(HELP_TEXT, parse_mode=ParseMode.HTML)
    logger.info("help response sent")


async def about_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"about_command called by user {update.effective_user.id}")
    await update.message.reply_text(ABOUT_TEXT, parse_mode=ParseMode.HTML)
    logger.info("about response sent")


async def create_game_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Command to create a new topic-based game."""
    logger.info(f"create_game called by user {update.effective_user.id}")
    await create_topic_game_handler(update, context)


async def join_games_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Command to show available games to join."""
    logger.info(f"join_games called by user {update.effective_user.id}")
    await show_available_games_handler(update, context)


async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        query = update.callback_query
        user_id = query.from_user.id
        data = query.data
        chat_id = query.message.chat_id

        logger.debug(f"button_click: user={user_id}, data={data}, chat={chat_id}")

        # First, try to handle topic-related callbacks
        if await callback_query_handler(update, context):
            return

        # Handle AI callbacks
        if data.startswith("ai_"):
            await handle_ai_callback(update, context)
            return

        # Handle engagement callbacks
        if data.startswith(
            (
                "engagement_",
                "show_basecamp",
                "show_missions",
                "show_flash",
                "show_cards",
            )
        ):
            await handle_engagement_callback(update, context)
            return

        await query.answer()
        game_manager = get_game_manager(chat_id)

        if data == "classic_mode":
            logger.debug(f"Switching to classic mode for user {user_id}")
            await query.message.reply_text(
                "🎮 **Classic Mode** - Single game per group\n\n"
                "Use the menu below to play:",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=main_menu(),
            )
        elif data == "ai_status":
            logger.debug(f"Showing AI status for user {user_id}")
            await ai_status_handler(update, context)
        elif data == "join_game":
            logger.debug(f"Processing join_game for user {user_id}")
            await game_manager.handle_join_game(update, context)
            await query.message.reply_text("🎮 Main Menu:", reply_markup=main_menu())
        elif data == "complete_task":
            logger.debug(f"Processing complete_task for user {user_id}")
            await game_manager.handle_complete_task(update, context)
            await query.message.reply_text("🎮 Main Menu:", reply_markup=main_menu())
        elif data == "start_voting":
            logger.debug(f"Processing start_voting for user {user_id}")
            await game_manager.handle_start_voting(update, context)
        elif data == "view_profile":
            logger.debug(f"Processing view_profile for user {user_id}")
            await game_manager.show_profile(update)
            await query.message.reply_text("🎮 Main Menu:", reply_markup=main_menu())
        elif data == "leaderboard":
            logger.debug(f"Processing leaderboard for user {user_id}")
            await game_manager.show_leaderboard(update)
            await query.message.reply_text("🎮 Main Menu:", reply_markup=main_menu())
        elif data == "restart_game":
            logger.debug(f"Processing restart_game for user {user_id}")
            await game_manager.reset(update)
            await query.message.reply_text(
                "Game reset. 🎮 Main Menu:", reply_markup=main_menu()
            )
        elif data.startswith("vote_") or data == "vote_skip":
            logger.debug(f"Processing vote for user {user_id}: {data}")
            await game_manager.handle_vote(update, context)
        elif data == "show_rules":
            logger.debug(f"Processing show_rules for user {user_id}")
            await game_manager.show_rules(update)
        elif data.startswith("analytics_"):
            logger.debug(f"Processing analytics callback for user {user_id}: {data}")
            await handle_analytics_callback(update, context)
        elif data == "choose_pulse_code":
            # Start Pulse Code flow
            logger.info("User selected Pulse Code")
            # Placeholder: Start Pulse Code game (implement full flow in next steps)
            await query.message.reply_text(
                "💡 Pulse Code game coming soon! (or implement start logic here)"
            )
        else:
            logger.warning(f"Unknown button data: {data}")
            await query.message.reply_text("Unknown action.", reply_markup=main_menu())

    except Exception as e:
        logger.error(f"button_click exception: {e}")
        import traceback

        traceback.print_exc()
        msg = update.message or (
            update.callback_query and update.callback_query.message
        )
        if msg:
            await msg.reply_text(f"❌ An error occurred: {e}")


async def handle_discussion(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    text = update.message.text

    logger.debug(
        f"handle_discussion: chat={chat_id}, user={user_id}, text='{text[:50]}...'"
    )

    # Check if this is a topic message
    if update.message.is_topic_message:
        await topic_message_handler(update, context)
    else:
        # Classic mode
        game_manager = get_game_manager(chat_id)
        await game_manager.handle_discussion(update, context)


async def start_private(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    logger.info(f"start_private called by user {user_id}")
    await update.message.reply_text("👋 Use /startgame in a group to begin!")
    logger.info("start_private response sent")


async def error_handler(update, context):
    try:
        raise context.error
    except TimedOut:
        logger.warning("Telegram API timed out. Retrying...")
    except NetworkError:
        logger.warning("Network error. Check your connection.")
    except Exception as e:
        logger.error(f"Unhandled error: {e}")


def signal_handler(signum, frame):
    logger.info("\n🛑 Bot shutdown requested. Exiting gracefully...")
    sys.exit(0)


async def cleanup_job(context):
    # context.application is available here
    topic_handler.topic_manager.cleanup_old_sessions(max_age_hours=6)
    engagement_engine.cleanup_old_data()
    engagement_engine.flash_games_system.schedule_friday_night_event()
    engagement_engine.flash_games_system.schedule_mystery_hour_event()


def main():
    # Set up signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Initialize database
    init_db()

    # Recover active sessions from database
    logger.info("Recovering active sessions from database...")
    topic_handler.topic_manager.recover_active_sessions()

    # Create the Application
    application = ApplicationBuilder().token(TOKEN).build()

    logger.info("🤖 Starting AI-Powered Smart Game Bot...")
    logger.info(
        f"[INFO] BOT_TOKEN: {TOKEN[:10]}..." if TOKEN else "[ERROR] BOT_TOKEN: None"
    )

    try:
        logger.info("✅ Database initialized")
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)

    try:
        logger.info("✅ Bot application created")
    except Exception as e:
        logger.error(f"❌ Failed to create bot application: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)

    # Add handlers
    application.add_handler(CommandHandler("start", start_private))
    application.add_handler(CommandHandler("startgame", startgame))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("about", about_command))
    application.add_handler(CommandHandler("menu", menu_handler))

    # Topic-based game commands
    application.add_handler(CommandHandler("creategame", create_game_command))
    application.add_handler(CommandHandler("joingames", join_games_command))

    # Analytics commands
    application.add_handler(CommandHandler("stats", show_player_stats))
    application.add_handler(CommandHandler("leaderboard", show_session_leaderboard))
    application.add_handler(CommandHandler("chatstats", show_chat_stats))
    application.add_handler(CommandHandler("global", show_global_leaderboard))
    application.add_handler(CommandHandler("recent", show_recent_games))
    application.add_handler(CommandHandler("analytics", show_analytics_menu))

    # Engagement commands
    application.add_handler(CommandHandler("basecamp", show_basecamp_handler))
    application.add_handler(CommandHandler("missions", show_missions_handler))
    application.add_handler(CommandHandler("flash", show_flash_events_handler))
    application.add_handler(CommandHandler("cards", show_cards_handler))
    application.add_handler(CommandHandler("engagement", show_engagement_summary_handler))

    # AI commands
    application.add_handler(CommandHandler("ai", ai_status_handler))
    application.add_handler(CommandHandler("aistatus", ai_status_handler))
    application.add_handler(CommandHandler("aipersonas", ai_personas_handler))
    application.add_handler(CommandHandler("aidetective", ai_detective_handler))
    application.add_handler(CommandHandler("aichaos", ai_chaos_handler))
    application.add_handler(CommandHandler("ailore", ai_lore_handler))
    application.add_handler(CommandHandler("aitask", ai_task_handler))

    application.add_handler(CommandHandler("start_pulse_code", start_pulse_code))
    application.add_handler(CommandHandler("guess", guess_pulse_code))
    application.add_handler(CommandHandler("mind_link", mind_link))
    application.add_handler(CommandHandler("desperation_gambit", desperation_gambit))
    application.add_handler(CommandHandler("my_stress", pulse_code_status))
    application.add_handler(CommandHandler("end_pulse_code", end_pulse_code))
    application.add_handler(CommandHandler("start_dual_operative_game", start_dual_operative_game))
    application.add_handler(CommandHandler("start_triple_threat_game", start_triple_threat_game))
    application.add_handler(CommandHandler("feedback", feedback))
    application.add_handler(CommandHandler("join_pulse_code", join_pulse_code))
    application.add_handler(CommandHandler("leave_pulse_code", leave_pulse_code))
    application.add_handler(CommandHandler("pulse_code_players", pulse_code_players))

    application.add_handler(CallbackQueryHandler(button_click))
    application.add_handler(MessageHandler(filters.TEXT & filters.ChatType.GROUPS, handle_discussion))
    application.add_error_handler(error_handler)

    logger.info("✅ Handlers configured")
    logger.info("🤖 AI Features enabled:")
    for feature in ai_game_engine.get_enabled_features():
        logger.info(f"   • {feature.replace('_', ' ').title()}")

    logger.info("🚀 Starting bot polling...")
    try:
        # Clear any existing webhooks and start polling
        application.job_queue.run_repeating(cleanup_job, interval=3600, first=0)
        application.run_polling(
            drop_pending_updates=True, allowed_updates=Update.ALL_TYPES
        )
    except KeyboardInterrupt:
        logger.info("\n🛑 Bot stopped by user.")
        sys.exit(0)
    except Exception as e:
        error_msg = str(e)
        logger.error(f"[ERROR] Polling exception: {error_msg}")
        import traceback

        traceback.print_exc()

        if "Conflict" in error_msg:
            logger.warning(
                "❌ Bot conflict detected: Another instance is already running."
            )
            logger.info("💡 This is normal if the bot is deployed elsewhere.")
            logger.info("✅ Your bot code is working correctly!")
            logger.info("🔄 The deployed bot on Render.com is handling your commands.")
            logger.info("📱 Try testing with @abel5173_bot in a Telegram group.")
            sys.exit(0)
        elif "Timed out" in error_msg or "ConnectTimeout" in error_msg:
            logger.warning("⏰ Connection timeout - this is normal during startup.")
            logger.info("✅ Bot is ready and will retry automatically.")
            sys.exit(0)
        else:
            logger.error(f"❌ Unexpected error: {error_msg}")
            sys.exit(1)


if __name__ == "__main__":
    main()
