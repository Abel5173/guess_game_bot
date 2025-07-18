import logging

logger = logging.getLogger(__name__)
from telegram import Update
from telegram.ext import ContextTypes
from bot.constants import HELP_TEXT


async def help_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.info(
        f"help_handler called by user {update.effective_user.id if update.effective_user else 'unknown'}"
    )
    if update.message is not None:
        await update.message.reply_text(HELP_TEXT, parse_mode="HTML")
