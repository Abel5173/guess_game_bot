import os
from telegram import Update, ParseMode
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


def main():
    init_db()  # Initialize tables
    app = (
        ApplicationBuilder()
        .token(TOKEN)
        .connect_timeout(60)
        .read_timeout(60)
        .write_timeout(60)
        .build()
    )
    app.add_handler(CommandHandler("start", start_private))
    app.add_handler(CommandHandler("startgame", startgame))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("about", about_command))
    app.add_handler(CallbackQueryHandler(button_click))
    app.add_handler(
        MessageHandler(filters.TEXT & filters.ChatType.GROUPS, handle_discussion)
    )

    print("🤖 Smart Game Bot Running...")
    app.run_polling()


if __name__ == "__main__":
    main()
