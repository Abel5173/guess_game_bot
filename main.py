from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler,
    MessageHandler, ContextTypes, filters
)
import os
from dotenv import load_dotenv
from bot.game_manager import GameManager
from bot.constants import HELP_TEXT, ABOUT_TEXT

load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")

games = {}  # chat_id: GameManager

def get_game_manager(chat_id):
    if chat_id not in games:
        games[chat_id] = GameManager()
    return games[chat_id]

def get_game_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🧠 Guess Game", callback_data="choose_guess")],
        [InlineKeyboardButton("🕵️ Impostor Game", callback_data="choose_impostor")],
    ])

async def startgame(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message or (update.callback_query and update.callback_query.message)
    if not msg:
        return
    await msg.reply_text(
        "🎮 <b>Choose a game to play:</b>",
        reply_markup=get_game_menu(),
        parse_mode=ParseMode.HTML
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(HELP_TEXT, parse_mode=ParseMode.HTML)

async def about_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(ABOUT_TEXT, parse_mode=ParseMode.HTML)

async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    chat_id = query.message.chat_id
    game_manager = get_game_manager(chat_id)
    if data == "choose_guess":
        game_manager.set_game("guess")
        await query.message.reply_text(
            "🧠 <b>Guess Game selected!</b>",
            parse_mode=ParseMode.HTML
        )
        await game_manager.get_game().startgame(update, context)
    elif data == "choose_impostor":
        game_manager.set_game("impostor")
        await query.message.reply_text(
            "🕵️ <b>Impostor Game selected!</b>",
            parse_mode=ParseMode.HTML
        )
        markup = InlineKeyboardMarkup([
            [InlineKeyboardButton("🙋 Join Impostor Game", callback_data="join_impostor")],
            [InlineKeyboardButton("🚦 Start Impostor Game", callback_data="start_impostor")],
        ])
        await query.message.reply_text(
            "🕵️ <b>Impostor Game started!</b>\n\nClick to join. Need at least 4 players.",
            reply_markup=markup,
            parse_mode=ParseMode.HTML
        )
    elif data == "join_impostor":
        if game_manager.get_type() == "impostor":
            await game_manager.get_game().join_impostor(update, context)
    elif data == "start_impostor":
        if game_manager.get_type() == "impostor":
            await game_manager.get_game().start_impostor_game(update, context)
    elif data == "join_guess" or data == "show_guess_rules":
        if game_manager.get_type() == "guess":
            await game_manager.get_game().button_click(update, context)

async def handle_secret(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    game_manager = get_game_manager(chat_id)
    if game_manager.get_type() == "guess":
        await game_manager.get_game().handle_secret(update, context)

async def handle_guess(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    game_manager = get_game_manager(chat_id)
    if game_manager.get_type() == "guess":
        await game_manager.get_game().handle_guess(update, context)

async def start_private(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Use /startgame in a group to begin!")

def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start_private))
    app.add_handler(CommandHandler("startgame", startgame))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("about", about_command))
    app.add_handler(CallbackQueryHandler(button_click))
    app.add_handler(MessageHandler(filters.TEXT & filters.ChatType.PRIVATE, handle_secret))
    app.add_handler(MessageHandler(filters.TEXT & filters.ChatType.GROUPS, handle_guess))
    print("🤖 Smart Game Bot Running...")
    app.run_polling()

if __name__ == "__main__":
    main() 