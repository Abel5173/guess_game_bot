from telegram import Update
from telegram.ext import ContextTypes
from .core import PulseCodeGame

# Dictionary to store game instances
pulse_code_games = {}

async def start_pulse_code_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Starts a new game of Pulse Code.
    """
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id

    if chat_id in pulse_code_games:
        await update.message.reply_text("A game is already in progress in this chat.")
        return

    # Create a new game instance
    game = PulseCodeGame(host_id=user_id, chat_id=chat_id, mode="architect")
    pulse_code_games[chat_id] = game
    game.start_game()

    await update.message.reply_text(
        "Pulse Code: Architect Protocol initiated.\n"
        "I have locked in my Pulse Code. Your turn to guess."
    )

async def make_guess_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handles a player's guess.
    """
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id

    if chat_id not in pulse_code_games:
        await update.message.reply_text("No game is currently active in this chat.")
        return

    game = pulse_code_games[chat_id]

    try:
        guess = context.args[0]
        hits, flashes, static = game.make_guess(user_id, "AI-Calculon", guess)

        if hits == 4:
            await update.message.reply_text(
                f"Congratulations! You've cracked the code {guess}. You win!"
            )
            del pulse_code_games[chat_id]
        else:
            await update.message.reply_text(
                f"Guess: {guess}\n"
                f"Hits: {hits}, Flashes: {flashes}, Static: {static}\n"
                f"Your Stress: {game.players[user_id]['stress']}%"
            )
    except (IndexError, ValueError) as e:
        await update.message.reply_text(f"Error: {e}")
