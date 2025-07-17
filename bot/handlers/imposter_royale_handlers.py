from telegram import Update
from telegram.ext import ContextTypes
from bot.imposter_royale.game import ImposterRoyaleGame

games = {}


def get_game(chat_id: int) -> ImposterRoyaleGame:
    if chat_id not in games:
        games[chat_id] = ImposterRoyaleGame(chat_id)
    return games[chat_id]


async def start_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    game = get_game(chat_id)
    await game.start_game()
    await update.message.reply_text(
        "Imposter Royale has begun! Roles have been assigned."
    )


async def join_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user = update.effective_user
    game = get_game(chat_id)
    await game.add_player(user.id, user.first_name)
    await update.message.reply_text(f"{user.first_name} has joined the game.")


async def move_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user = update.effective_user
    game = get_game(chat_id)
    room = context.args[0]
    await game.move_player(user.id, room)
    await update.message.reply_text(f"{user.first_name} has moved to {room}.")


async def kill_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    killer = update.effective_user
    game = get_game(chat_id)
    victim_username = context.args[0]
    # Logic to get victim_id from username...
    # await game.kill_player(killer.id, victim_id)
    await update.message.reply_text(f"{killer.first_name} attempts a kill...")


async def report_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    reporter = update.effective_user
    game = get_game(chat_id)
    # Logic to identify the victim...
    # await game.report_body(reporter.id, victim_id)
    await update.message.reply_text(
        "A body has been reported! A meeting will now commence."
    )


async def vote_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    voter = update.effective_user
    game = get_game(chat_id)
    target_username = context.args[0]
    # Logic to get target_id from username...
    # await game.handle_vote(voter.id, target_id)
    await update.message.reply_text(f"{voter.first_name} has cast their vote.")


async def express_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user = update.effective_user
    game = get_game(chat_id)
    expression = context.args[0]
    analysis = await game.ai_manager.analyze_expression(expression)
    await update.message.reply_text(
        f"{user.first_name} expresses: {expression}\nAI Analysis: {analysis}"
    )
