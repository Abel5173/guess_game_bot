import logging

logger = logging.getLogger(__name__)
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes


async def menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.info(
        f"menu_handler called by user {update.effective_user.id if update.effective_user else 'unknown'}"
    )
    keyboard = [
        [InlineKeyboardButton("🕵️ Impostor Game", callback_data="choose_impostor")]
    ]
    markup = InlineKeyboardMarkup(keyboard)
    if update.message is not None:
        await update.message.reply_text(
            "🎮 <b>Choose a game to play:</b>", reply_markup=markup, parse_mode="HTML"
        )
