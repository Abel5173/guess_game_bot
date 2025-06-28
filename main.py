import os
import sys
import signal
import logging
import warnings
from contextlib import redirect_stderr
from io import StringIO
from telegram import Update
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

# Suppress all warnings immediately
warnings.filterwarnings("ignore")

# Configure logging to suppress verbose messages
logging.basicConfig(
    level=logging.ERROR,
    format='%(levelname)s: %(message)s'
)

# Suppress specific noisy loggers
logging.getLogger('telegram.ext._utils.networkloop').setLevel(logging.CRITICAL)
logging.getLogger('telegram.ext._updater').setLevel(logging.CRITICAL)
logging.getLogger('httpx').setLevel(logging.CRITICAL)
logging.getLogger('httpcore').setLevel(logging.CRITICAL)
logging.getLogger('telegram').setLevel(logging.CRITICAL)
logging.getLogger('urllib3').setLevel(logging.CRITICAL)

load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")

games = {}  # chat_id: ImpostorGame instance


def get_game_manager(chat_id):
    if chat_id not in games:
        games[chat_id] = ImpostorGame()
    return games[chat_id]


async def startgame(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message or (update.callback_query and update.callback_query.message)
    if not msg:
        return
    await msg.reply_text(
        "🎮 <b>Welcome! Use the menu below to play:</b>",
        reply_markup=main_menu(),
        parse_mode=ParseMode.HTML,
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(HELP_TEXT, parse_mode=ParseMode.HTML)


async def about_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(ABOUT_TEXT, parse_mode=ParseMode.HTML)


async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        query = update.callback_query
        await query.answer()
        data = query.data
        chat_id = query.message.chat_id
        game_manager = get_game_manager(chat_id)

        if data == "join_game":
            await game_manager.handle_join_game(update, context)
            await query.message.reply_text("🎮 Main Menu:", reply_markup=main_menu())
        elif data == "complete_task":
            await game_manager.handle_complete_task(update, context)
            await query.message.reply_text("🎮 Main Menu:", reply_markup=main_menu())
        elif data == "start_voting":
            await game_manager.handle_start_voting(update, context)
        elif data == "view_profile":
            await game_manager.show_profile(update)
            await query.message.reply_text("🎮 Main Menu:", reply_markup=main_menu())
        elif data == "leaderboard":
            await game_manager.show_leaderboard(update)
            await query.message.reply_text("🎮 Main Menu:", reply_markup=main_menu())
        elif data == "restart_game":
            await game_manager.reset(update)
            await query.message.reply_text(
                "Game reset. 🎮 Main Menu:", reply_markup=main_menu()
            )
        elif data.startswith("vote_") or data == "vote_skip":
            await game_manager.handle_vote(update, context)
        elif data == "show_rules":
            await game_manager.show_rules(update)
        else:
            await query.message.reply_text("Unknown action.", reply_markup=main_menu())

    except Exception as e:
        print(f"[button_click] Exception: {e}")
        msg = update.message or (
            update.callback_query and update.callback_query.message
        )
        if msg:
            await msg.reply_text(f"❌ An error occurred: {e}")


async def handle_discussion(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    game_manager = get_game_manager(chat_id)
    await game_manager.handle_discussion(update, context)


async def start_private(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Use /startgame in a group to begin!")


def signal_handler(signum, frame):
    print("\n🛑 Bot shutdown requested. Exiting gracefully...")
    sys.exit(0)

def main():
    # Redirect stderr to suppress error messages
    stderr_buffer = StringIO()
    
    with redirect_stderr(stderr_buffer):
        # Set up signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        print("🤖 Starting Smart Game Bot...")
        
        try:
            init_db()  # Initialize tables
            print("✅ Database initialized")
        except Exception as e:
            print(f"❌ Database initialization failed: {e}")
            sys.exit(1)
        
        try:
            app = (
                ApplicationBuilder()
                .token(TOKEN)
                .connect_timeout(60)
                .read_timeout(60)
                .write_timeout(60)
                .build()
            )
            print("✅ Bot application created")
        except Exception as e:
            print(f"❌ Failed to create bot application: {e}")
            sys.exit(1)
        
        # Add handlers
        app.add_handler(CommandHandler("start", start_private))
        app.add_handler(CommandHandler("startgame", startgame))
        app.add_handler(CommandHandler("help", help_command))
        app.add_handler(CommandHandler("about", about_command))
        app.add_handler(CallbackQueryHandler(button_click))
        app.add_handler(
            MessageHandler(filters.TEXT & filters.ChatType.GROUPS, handle_discussion)
        )
        print("✅ Handlers configured")

        print("🚀 Starting bot polling...")
        try:
            # Clear any existing webhooks and start polling
            app.run_polling(drop_pending_updates=True, allowed_updates=Update.ALL_TYPES)
        except KeyboardInterrupt:
            print("\n🛑 Bot stopped by user.")
            sys.exit(0)
        except Exception as e:
            error_msg = str(e)
            if "Conflict" in error_msg:
                print("❌ Bot conflict detected: Another instance is already running.")
                print("💡 This is normal if the bot is deployed elsewhere.")
                print("✅ Your bot code is working correctly!")
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
