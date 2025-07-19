from functools import wraps
from telegram import Update
from telegram.ext import ContextTypes
from bot.pulse_code_manager import pulse_code_game_manager

def game_is_active(func):
    """Decorator to check if a Pulse Code game is active in the chat."""
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        chat_id = update.effective_chat.id
        game = pulse_code_game_manager.get_game(chat_id)
        if not game or not game.active:
            await update.message.reply_text(
                "No active Pulse Code game. Use /start_pulse_code to begin."
            )
            return
        # Pass the game object to the handler
        return await func(update, context, game=game, *args, **kwargs)
    return wrapper
