import logging

logger = logging.getLogger(__name__)
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes


async def menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.info(f"menu_handler called by user {update.effective_user.id if update.effective_user else 'unknown'}")
    keyboard = [
        [InlineKeyboardButton("🕵️ Impostor Game", callback_data="choose_impostor")],
        [InlineKeyboardButton("💡 Pulse Code", callback_data="choose_pulse_code")],
        # Uncomment the next line if Guess Game is implemented
        # [InlineKeyboardButton("🔤 Guess Game", callback_data="choose_guess")],
    ]
    markup = InlineKeyboardMarkup(keyboard)
    text = (
        "<b>🎮 Choose a Game to Play:</b>\n\n"
        "<b>🕵️ Impostor Game:</b> Social deduction, deception, and AI-powered intrigue.\n"
        "<b>💡 Pulse Code:</b> High-stakes code-breaking with AI personalities and stress mechanics.\n"
        # + "<b>🔤 Guess Game:</b> Classic word/number guessing challenge.\n"
    )
    if update.message is not None:
        await update.message.reply_text(text, reply_markup=markup, parse_mode="HTML")
    elif update.callback_query is not None:
        await update.callback_query.message.reply_text(text, reply_markup=markup, parse_mode="HTML")
