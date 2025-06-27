from telegram import Update
from telegram.ext import ContextTypes
from bot.constants import HELP_TEXT

async def help_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(HELP_TEXT, parse_mode='HTML') 