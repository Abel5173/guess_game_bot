import logging

logger = logging.getLogger(__name__)
from telegram import Update
from telegram.ext import ContextTypes
from bot.impostor import ImpostorGame

# Dictionary to manage game instances per group chat
impostor_games = {}


def get_game(chat_id: int) -> ImpostorGame:
    if chat_id not in impostor_games:
        impostor_games[chat_id] = ImpostorGame()
    return impostor_games[chat_id]


async def join_impostor_handler(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Handler for joining the Impostor Game."""
    if update.effective_chat is not None:
        chat_id = update.effective_chat.id
        game = get_game(chat_id)
        await game.join_impostor(update, context)


async def start_impostor_game_handler(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Handler for starting the Impostor Game."""
    if update.effective_chat is not None:
        chat_id = update.effective_chat.id
        game = get_game(chat_id)
        await game.start_impostor_game(update, context)


async def discussion_handler(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Handler for group discussion messages during the discussion phase."""
    if update.effective_chat is not None:
        chat_id = update.effective_chat.id
        game = get_game(chat_id)
        await game.handle_discussion(update, context)


async def vote_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handler for voting actions during the voting phase."""
    if update.effective_chat is not None:
        chat_id = update.effective_chat.id
        game = get_game(chat_id)
        await game.handle_vote(update, context)


async def status_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handler to show the current game status."""
    if update.effective_chat is not None:
        chat_id = update.effective_chat.id
        game = get_game(chat_id)
        await game.show_main_menu(update)


async def profile_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_chat is not None:
        chat_id = update.effective_chat.id
        game = get_game(chat_id)
        await game.show_profile(update)


async def reset_game_handler(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Handler to reset the game in a group chat."""
    if update.effective_chat is not None:
        chat_id = update.effective_chat.id
        if chat_id in impostor_games:
            impostor_games[chat_id].reset()
            if update.message is not None:
                await update.message.reply_text("🔄 Game has been reset.")
        else:
            if update.message is not None:
                await update.message.reply_text("No game to reset.")


async def leaderboard_handler(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    if update.effective_chat is not None:
        chat_id = update.effective_chat.id
        game = get_game(chat_id)
        await game.show_leaderboard(update)
