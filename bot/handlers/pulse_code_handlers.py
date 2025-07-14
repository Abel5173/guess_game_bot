from telegram import Update
from telegram.ext import ContextTypes
from bot.pulse_code.game import PulseCodeGame

games = {}

def get_game(chat_id: int) -> PulseCodeGame:
    if chat_id not in games:
        games[chat_id] = PulseCodeGame()
    return games[chat_id]

async def start_pulse_code_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # This will be expanded to allow choosing a game mode
    chat_id = update.effective_chat.id
    game = get_game(chat_id)
    user = update.effective_user
    game.start_architect_game(user.id, user.first_name)
    await update.message.reply_text("Pulse Code: Architect Protocol initiated. I have my code. Your turn to guess.")

async def guess_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    game = get_game(chat_id)
    user = update.effective_user
    try:
        guess_str = context.args[0]
        guess_code = [int(d) for d in guess_str]

        # In architect mode, the target is always the bot
        target_id = "PulseCodeBot"

        hits, flashes, static = game.core.make_guess(user.id, target_id, guess_code)

        response = f"Guess: {guess_str}\n"
        response += f"Hits: {hits}, Flashes: {flashes}, Static: {static}\n"
        response += f"System Stress: {game.core.players[user.id]['system_stress']}%"

        await update.message.reply_text(response)

        if hits == game.core.config["code_length"]:
            await update.message.reply_text("Congratulations! You've cracked the Pulse Code!")
            del games[chat_id]

    except (IndexError, ValueError):
        await update.message.reply_text("Invalid guess format. Please use a 4-digit number, e.g., /guess 1234")
