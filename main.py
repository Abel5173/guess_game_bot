import os
import sys
import signal
import logging
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
)
from bot.database import init_db
from dotenv import load_dotenv
from bot.impostor import ImpostorGame
from bot.constants import HELP_TEXT, ABOUT_TEXT
from bot.topic_manager import topic_handler
from bot.engagement import engagement_engine
from bot.ai import ai_game_engine
from bot.handlers import register_handlers
from bot.handlers.game_selection_handlers import start_game_selection
from telegram.error import TimedOut, NetworkError
from bot.database.session_manager import list_active_games, delete_game
from bot.database import get_session
import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)

# Suppress noisy loggers
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


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(HELP_TEXT, parse_mode=ParseMode.HTML)


async def about_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(ABOUT_TEXT, parse_mode=ParseMode.HTML)


async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # This function is now a placeholder for any non-module-specific callbacks
    query = update.callback_query
    await query.answer()
    await query.message.reply_text("Unknown action.")


async def handle_discussion(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.is_topic_message:
        await topic_message_handler(update, context)
    else:
        game_manager = get_game_manager(update.effective_chat.id)
        await game_manager.handle_discussion(update, context)


async def start_private(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Use /startgame in a group to begin!")


async def error_handler(update, context):
    try:
        raise context.error
    except (TimedOut, NetworkError):
        logger.warning("Network error occurred.")
    except Exception as e:
        logger.error(f"Unhandled error: {e}", exc_info=True)


def signal_handler(signum, frame):
    logger.info("🛑 Bot shutdown requested. Exiting gracefully...")
    sys.exit(0)


async def cleanup_job(context):
    topic_handler.topic_manager.cleanup_old_sessions(max_age_hours=6)
    engagement_engine.cleanup_old_data()


async def cleanup_inactive_games(context):
    """Periodic job to clean up inactive games."""
    now = datetime.datetime.utcnow()
    timeout = datetime.timedelta(hours=1)
    ended_chats = []
    with get_session() as session:
        for game in list_active_games(session):
            if now - game.last_activity > timeout:
                delete_game(session, game.chat_id)
                ended_chats.append(game.chat_id)
    # Optionally, notify chats (if possible)
    for chat_id in ended_chats:
        try:
            await context.bot.send_message(chat_id, "Game ended due to inactivity (1 hour timeout). Start a new game anytime!")
        except Exception:
            pass


def main():
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    init_db()
    logger.info("✅ Database initialized")

    topic_handler.topic_manager.recover_active_sessions()
    logger.info("✅ Active sessions recovered")

    application = ApplicationBuilder().token(TOKEN).build()
    logger.info("✅ Bot application created")

    # We now pass the start_game_selection function directly
    register_handlers(application, start_game_selection)
    logger.info("✅ Handlers configured")

    logger.info("🤖 AI Features enabled:")
    for feature in ai_game_engine.get_enabled_features():
        logger.info(f"   • {feature.replace('_', ' ').title()}")

    logger.info("🚀 Starting bot polling...")
    try:
        application.job_queue.run_repeating(cleanup_job, interval=3600, first=0)
        application.job_queue.run_repeating(cleanup_inactive_games, interval=600, first=0)
        application.run_polling(drop_pending_updates=True)
    except Exception as e:
        logger.critical(f"❌ Bot failed to start: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()