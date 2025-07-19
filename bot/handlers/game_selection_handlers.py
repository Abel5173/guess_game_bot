import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from bot.handlers.pulse_code_handlers import start_pulse_code

logger = logging.getLogger(__name__)

async def start_game_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Sends a message with two inline buttons to choose a game."""
    keyboard = [
        [
            InlineKeyboardButton("Pulse-Code", callback_data="select_game_pulse"),
            InlineKeyboardButton("Imposter", callback_data="select_game_imposter"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Please choose a game to play:", reply_markup=reply_markup)


async def handle_game_selection_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the user's game selection."""
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "select_game_pulse":
        await query.edit_message_text(text="You selected Pulse-Code.")
        # Now, show the pulse code mode selection
        await start_pulse_code(update, context)
    elif data == "select_game_imposter":
        await query.edit_message_text(text="Imposter game is coming soon!")
