from telegram import Update
from telegram.ext import ContextTypes
from bot.game.engine import ImposterRoyaleEngine

engine = ImposterRoyaleEngine()

async def start_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    await engine.start_game(chat_id)
    await update.message.reply_text("Imposter Royale has begun! Roles have been assigned.")

async def join_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user = update.effective_user
    await engine.add_player(chat_id, user.id, user.first_name)
    await update.message.reply_text(f"{user.first_name} has joined the game.")

async def move_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user = update.effective_user
    room = context.args[0]
    await engine.move_player(chat_id, user.id, room)
    await update.message.reply_text(f"{user.first_name} has moved to {room}.")

async def kill_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    killer = update.effective_user
    victim_username = context.args[0]
    # Logic to get victim_id from username
    # await engine.kill(chat_id, killer.id, victim_id)
    await update.message.reply_text(f"{killer.first_name} attempts a kill...")

async def report_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    reporter = update.effective_user
    # Logic to identify the victim
    # await engine.report(chat_id, reporter.id, victim_id)
    await update.message.reply_text("A body has been reported! A meeting will now commence.")

async def vote_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    voter = update.effective_user
    target_username = context.args[0]
    # Logic to get target_id from username
    # await engine.vote(chat_id, voter.id, target_id)
    await update.message.reply_text(f"{voter.first_name} has cast their vote.")
