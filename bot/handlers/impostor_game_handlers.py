from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.constants import ParseMode
from telegram.ext import ContextTypes
from bot.impostor import ImpostorGame

# Dictionary to manage game instances per group chat
impostor_games = {}

def get_game(chat_id):
    if chat_id not in impostor_games:
        impostor_games[chat_id] = ImpostorGame()
    return impostor_games[chat_id]

async def join_impostor_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for joining the Impostor Game."""
    chat_id = update.effective_chat.id
    game = get_game(chat_id)
    await game.join_impostor(update, context)

async def start_impostor_game_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for starting the Impostor Game."""
    chat_id = update.effective_chat.id
    game = get_game(chat_id)
    await game.start_impostor_game(update, context)

async def discussion_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for group discussion messages during the discussion phase."""
    chat_id = update.effective_chat.id
    game = get_game(chat_id)
    await game.handle_discussion(update, context)

async def vote_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for voting actions during the voting phase."""
    chat_id = update.effective_chat.id
    game = get_game(chat_id)
    await game.handle_vote(update, context)

async def status_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler to show the current game status."""
    chat_id = update.effective_chat.id
    game = get_game(chat_id)
    await game.show_status(update)

async def profile_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    game = get_game(chat_id)
    await game.show_profile(update)

async def reset_game_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler to reset the game in a group chat."""
    chat_id = update.effective_chat.id
    if chat_id in impostor_games:
        impostor_games[chat_id].reset()
        await update.message.reply_text("🔄 Game has been reset.")
    else:
        await update.message.reply_text("No game to reset.")

async def leaderboard_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    game = get_game(chat_id)
    await game.show_leaderboard(update) 