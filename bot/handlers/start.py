import logging

logger = logging.getLogger(__name__)
from telegram import Update
from telegram.ext import ContextTypes


async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.info(
        f"start_handler called by user {update.effective_user.id if update.effective_user else 'unknown'}"
    )
    if update.effective_chat is not None and update.effective_chat.type == "private":
        if update.message is not None:
            await update.message.reply_text(
                "👋 Welcome! To play the Impostor Game, add me to a group and use /startgame."
            )
    else:
        if update.message is not None:
            await update.message.reply_text(
                "👋 Use /startgame to begin the Impostor Game in this group!"
            )
