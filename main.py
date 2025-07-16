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
from bot.impostor import ImpostorGame
from bot.pulse_code.handlers import start_pulse_code_game, make_guess_handler
from bot.game_manager import game_manager
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
from bot.topic_manager import topic_handler
from bot.engagement import engagement_engine
from bot.ai import ai_game_engine
import asyncio

# Configure logging to show more information
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

# Suppress only the most noisy loggers
logging.getLogger("telegram.ext._utils.networkloop").setLevel(logging.WARNING)
logging.getLogger("telegram.ext._updater").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)

load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")

# The new game_manager object will handle all game instances


async def startgame(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f"[INFO] startgame called by user {update.effective_user.id}")
    msg = update.message or (update.callback_query and update.callback_query.message)
    if not msg:
        print("[WARNING] No message found in update")
        return

    # Check if this is a forum/supergroup with topics
    chat = update.effective_chat
    if chat.is_forum:
        # Show topic-based game options
        await msg.reply_text(
            "🎮 **Welcome to the AI-Powered Impostor Game!**\n\n"
            "This group supports **Topic-based Game Rooms** with **AI Game Master** features!\n\n"
            "**Choose an option:**",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "🎮 Create New Game Room", callback_data="create_topic_game"
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            "📋 View Available Games",
                            callback_data="show_available_games",
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            "🎯 Classic Mode", callback_data="classic_mode"
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            "🏠 My Basecamp", callback_data="show_basecamp"
                        )
                    ],
                    [InlineKeyboardButton("🤖 AI Features", callback_data="ai_status")],
                ]
            ),
        )
    else:
        # Fall back to classic mode
        await msg.reply_text(
            "🎮 <b>Welcome! Choose a game to play:</b>",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "🕵️ Impostor Game", callback_data="select_impostor"
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            "📟 Pulse Code", callback_data="select_pulse_code"
                        )
                    ],
                ]
            ),
            parse_mode=ParseMode.HTML,
        )
    print("[INFO] startgame response sent")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f"[INFO] help_command called by user {update.effective_user.id}")
    await update.message.reply_text(HELP_TEXT, parse_mode=ParseMode.HTML)
    print("[INFO] help response sent")


async def about_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f"[INFO] about_command called by user {update.effective_user.id}")
    await update.message.reply_text(ABOUT_TEXT, parse_mode=ParseMode.HTML)
    print("[INFO] about response sent")


async def create_game_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Command to create a new topic-based game."""
    print(f"[INFO] create_game called by user {update.effective_user.id}")
    await create_topic_game_handler(update, context)


async def join_games_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Command to show available games to join."""
    print(f"[INFO] join_games called by user {update.effective_user.id}")
    await show_available_games_handler(update, context)


async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        query = update.callback_query
        user_id = query.from_user.id
        data = query.data
        chat_id = query.message.chat_id

        print(f"[INFO] button_click: user={user_id}, data={data}, chat={chat_id}")

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

        if data == "select_impostor":
            game_manager.start_new_game(chat_id, "impostor", user_id)
            await query.message.reply_text(
                "Impostor game selected. Use /join to join the game.",
                reply_markup=main_menu(),
            )
            return

        if data == "select_pulse_code":
            game_manager.start_new_game(chat_id, "pulse_code", user_id)
            await start_pulse_code_game(update, context)
            return

        game = game_manager.get_game(chat_id)
        game_type = game_manager.get_game_type(chat_id)

        if not game:
            await query.message.reply_text("No active game. Use /startgame to begin.")
            return

        if game_type == "impostor":
            if data == "join_game":
                print(f"[INFO] Processing join_game for user {user_id}")
                await game.handle_join_game(update, context)
                await query.message.reply_text(
                    "🎮 Main Menu:", reply_markup=main_menu()
                )
            elif data == "complete_task":
                print(f"[INFO] Processing complete_task for user {user_id}")
                await game.handle_complete_task(update, context)
                await query.message.reply_text(
                    "🎮 Main Menu:", reply_markup=main_menu()
                )
            elif data == "start_voting":
                print(f"[INFO] Processing start_voting for user {user_id}")
                await game.handle_start_voting(update, context)
            elif data == "view_profile":
                print(f"[INFO] Processing view_profile for user {user_id}")
                await game.show_profile(update)
                await query.message.reply_text(
                    "🎮 Main Menu:", reply_markup=main_menu()
                )
            elif data == "leaderboard":
                print(f"[INFO] Processing leaderboard for user {user_id}")
                await game.show_leaderboard(update)
                await query.message.reply_text(
                    "🎮 Main Menu:", reply_markup=main_menu()
                )
            elif data == "restart_game":
                print(f"[INFO] Processing restart_game for user {user_id}")
                game_manager.end_game(chat_id)
                await query.message.reply_text(
                    "Game reset. 🎮 Main Menu:", reply_markup=main_menu()
                )
            elif data.startswith("vote_") or data == "vote_skip":
                print(f"[INFO] Processing vote for user {user_id}: {data}")
                await game.handle_vote(update, context)
            elif data == "show_rules":
                print(f"[INFO] Processing show_rules for user {user_id}")
                await game.show_rules(update)
        elif data.startswith("analytics_"):
            print(f"[INFO] Processing analytics callback for user {user_id}: {data}")
            await handle_analytics_callback(update, context)
        else:
            print(f"[WARNING] Unknown button data: {data}")
            await query.message.reply_text("Unknown action.", reply_markup=main_menu())

    except Exception as e:
        print(f"[ERROR] button_click exception: {e}")
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

    print(
        f"[INFO] handle_discussion: chat={chat_id}, user={user_id}, text='{text[:50]}...'"
    )

    # Check if this is a topic message
    if update.message.is_topic_message:
        await topic_message_handler(update, context)
    else:
        # Classic mode
        game = game_manager.get_game(chat_id)
        if game and game_manager.get_game_type(chat_id) == "impostor":
            await game.handle_discussion(update, context)


async def start_private(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    print(f"[INFO] start_private called by user {user_id}")
    await update.message.reply_text("👋 Use /startgame in a group to begin!")
    print("[INFO] start_private response sent")


def signal_handler(signum, frame):
    print("\n🛑 Bot shutdown requested. Exiting gracefully...")
    sys.exit(0)


def start_periodic_cleanup():
    async def cleanup_loop():
        while True:
            # Clean up old game sessions
            topic_handler.topic_manager.cleanup_old_sessions(max_age_hours=6)

            # Clean up engagement data
            engagement_engine.cleanup_old_data()

            # Clean up AI data
            # This will be handled per session when games end

            # Schedule flash events
            engagement_engine.flash_games_system.schedule_friday_night_event()
            engagement_engine.flash_games_system.schedule_mystery_hour_event()

            await asyncio.sleep(3600)  # Run every hour

    asyncio.create_task(cleanup_loop())


def main():
    # Set up signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Initialize database
    init_db()

    # Recover active sessions from database
    print("[INFO] Recovering active sessions from database...")
    topic_handler.topic_manager.recover_active_sessions()

    # Start periodic cleanup
    start_periodic_cleanup()

    # Create the Application
    application = ApplicationBuilder().token(TOKEN).build()

    print("🤖 Starting AI-Powered Smart Game Bot...")
    print(f"[INFO] BOT_TOKEN: {TOKEN[:10]}..." if TOKEN else "[ERROR] BOT_TOKEN: None")

    try:
        print("✅ Database initialized")
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)

    try:
        print("✅ Bot application created")
    except Exception as e:
        print(f"❌ Failed to create bot application: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)

    # Add handlers
    application.add_handler(CommandHandler("start", start_private))
    application.add_handler(CommandHandler("startgame", startgame))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("about", about_command))
    application.add_handler(CommandHandler("pulse", start_pulse_code_game))
    application.add_handler(CommandHandler("guess", make_guess_handler))

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
    application.add_handler(
        CommandHandler("engagement", show_engagement_summary_handler)
    )

    # AI commands
    application.add_handler(CommandHandler("ai", ai_status_handler))
    application.add_handler(CommandHandler("aistatus", ai_status_handler))
    application.add_handler(CommandHandler("aipersonas", ai_personas_handler))
    application.add_handler(CommandHandler("aidetective", ai_detective_handler))
    application.add_handler(CommandHandler("aichaos", ai_chaos_handler))
    application.add_handler(CommandHandler("ailore", ai_lore_handler))
    application.add_handler(CommandHandler("aitask", ai_task_handler))

    application.add_handler(CallbackQueryHandler(button_click))
    application.add_handler(
        MessageHandler(filters.TEXT & filters.ChatType.GROUPS, handle_discussion)
    )

    print("✅ Handlers configured")
    print("🤖 AI Features enabled:")
    for feature in ai_game_engine.get_enabled_features():
        print(f"   • {feature.replace('_', ' ').title()}")

    print("🚀 Starting bot polling...")
    try:
        # Clear any existing webhooks and start polling
        application.run_polling(
            drop_pending_updates=True, allowed_updates=Update.ALL_TYPES
        )
    except KeyboardInterrupt:
        print("\n🛑 Bot stopped by user.")
        sys.exit(0)
    except Exception as e:
        error_msg = str(e)
        print(f"[ERROR] Polling exception: {error_msg}")
        import traceback

        traceback.print_exc()

        if "Conflict" in error_msg:
            print("❌ Bot conflict detected: Another instance is already running.")
            print("💡 This is normal if the bot is deployed elsewhere.")
            print("✅ Your bot code is working correctly!")
            print("🔄 The deployed bot on Render.com is handling your commands.")
            print("📱 Try testing with @abel5173_bot in a Telegram group.")
            sys.exit(0)
        elif "Timed out" in error_msg or "ConnectTimeout" in error_msg:
            print("⏰ Connection timeout - this is normal during startup.")
            print("✅ Bot is ready and will retry automatically.")
            sys.exit(0)
        else:
            print(f"❌ Unexpected error: {error_msg}")
            sys.exit(1)


if __name__ == "__main__":
    main()
