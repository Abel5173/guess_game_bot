from telegram import Update
from telegram.ext import ContextTypes


async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == "private":
        await update.message.reply_text(
            "👋 Welcome! To play the Impostor Game, add me to a group and use /startgame."
        )
    else:
        await update.message.reply_text(
            "👋 Use /startgame to begin the Impostor Game in this group!"
        )
