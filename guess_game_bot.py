import asyncio
import os
from dotenv import load_dotenv
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup
)
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler,
    MessageHandler, ContextTypes, filters
)

load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")

class GameSession:
    def __init__(self):
        self.players = {}  # user_id -> {'name': str, 'secret': str, 'ready': bool}
        self.group_chat_id = None
        self.started = False
        self.turn = None
        self.guess_counts = {}
        self.timeout_task = None

    def add_player(self, user_id, name):
        if len(self.players) < 2 and user_id not in self.players:
            self.players[user_id] = {'name': name, 'secret': None, 'ready': False}
            self.guess_counts[user_id] = 0
            return True
        return False

    def set_secret(self, user_id, secret):
        if user_id in self.players:
            self.players[user_id]['secret'] = secret
            self.players[user_id]['ready'] = True

    def is_ready(self):
        return len(self.players) == 2 and all(p['ready'] for p in self.players.values())

    def get_opponent_id(self, user_id):
        for uid in self.players:
            if uid != user_id:
                return uid
        return None

    def score_guess(self, guess, target):
        N = sum(1 for digit in guess if digit in target)
        O = sum(1 for g, t in zip(guess, target) if g == t)
        return N, O

    def reset(self):
        if self.timeout_task:
            self.timeout_task.cancel()
        self.__init__()


game = GameSession()

# === Handlers ===

async def startgame(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    if chat.type not in ["group", "supergroup"]:
        await update.message.reply_text("⚠️ Use /startgame inside a group chat.")
        return

    game.reset()
    game.group_chat_id = chat.id

    keyboard = [
        [InlineKeyboardButton("🎮 Join Game", callback_data="join_game")],
        [InlineKeyboardButton("📜 View Rules", callback_data="show_rules")]
    ]
    markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text("👾 New game started!\nPlayers, click below to join:", reply_markup=markup)


async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user = query.from_user

    if query.data == "join_game":
        if game.add_player(user.id, user.first_name):
            await query.message.reply_text(
                f"{user.first_name} joined! 🎉\nNow DM me your 4-digit secret number."
            )
            await context.bot.send_message(
                chat_id=user.id,
                text="🔒 Send your 4-digit secret number."
            )
        else:
            await query.message.reply_text("❌ Game already has 2 players or you already joined.")

    elif query.data == "show_rules":
        await query.message.reply_text(
            "📜 *Game Rules:*\n"
            "- Choose a 4-digit number\n"
            "- Take turns guessing your opponent's number\n"
            "- N = correct digits, O = correct position\n"
            "- First to guess wins\n"
            "- 60s timeout per turn\n"
            "- You can give up anytime",
            parse_mode="Markdown"
        )

    elif query.data.startswith("giveup_"):
        loser_id = int(query.data.split("_")[1])
        winner_id = game.get_opponent_id(loser_id)
        if not winner_id:
            return
        loser_name = game.players[loser_id]['name']
        winner_name = game.players[winner_id]['name']
        await context.bot.send_message(
            chat_id=game.group_chat_id,
            text=f"🆘 {loser_name} gave up! {winner_name} wins! 🏆"
        )
        game.reset()


async def handle_secret(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    text = update.message.text.strip()
    if update.message.chat.type != 'private':
        return
    if user.id in game.players and not game.players[user.id]['ready']:
        if len(text) == 4 and text.isdigit():
            game.set_secret(user.id, text)
            await update.message.reply_text("✅ Secret number set.")
            if game.is_ready():
                ids = list(game.players.keys())
                game.turn = ids[0]
                p1 = game.players[ids[0]]['name']
                p2 = game.players[ids[1]]['name']

                # Add Give Up Buttons
                keyboard = [
                    [InlineKeyboardButton(f"🆘 {p1} Give Up", callback_data=f"giveup_{ids[0]}")],
                    [InlineKeyboardButton(f"🆘 {p2} Give Up", callback_data=f"giveup_{ids[1]}")]
                ]
                markup = InlineKeyboardMarkup(keyboard)

                await context.bot.send_message(
                    chat_id=game.group_chat_id,
                    text=f"🔥 Game started between {p1} and {p2}!\n🎯 {p1} goes first.",
                    reply_markup=markup
                )

                game.started = True
                game.timeout_task = asyncio.create_task(start_turn_timer(context))
        else:
            await update.message.reply_text("⚠️ Enter a valid 4-digit number.")


async def handle_guess(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    text = update.message.text.strip()

    if not game.started or update.message.chat_id != game.group_chat_id:
        return

    if user_id not in game.players or game.turn != user_id:
        return await update.message.reply_text("⛔ It's not your turn!")

    if not text.isdigit() or len(text) != 4:
        return await update.message.reply_text("⚠️ Please enter a valid 4-digit number.")

    opponent_id = game.get_opponent_id(user_id)
    opponent_secret = game.players[opponent_id]['secret']
    N, O = game.score_guess(text, opponent_secret)
    game.guess_counts[user_id] += 1
    count = game.guess_counts[user_id]

    await context.bot.send_message(
        chat_id=game.group_chat_id,
        text=(
            f"🎯 {user.first_name} guessed `{text}` → N = {N}, O = {O}\n"
            f"📊 Total guesses: {count}"
        ),
        parse_mode="Markdown"
    )

    if text == opponent_secret:
        await context.bot.send_message(
            chat_id=game.group_chat_id,
            text=f"🏆 {user.first_name} WON by guessing `{text}` in {count} attempts! 🎉"
        )
        game.reset()
        return

    # Switch turn
    game.turn = opponent_id
    await context.bot.send_message(
        chat_id=game.group_chat_id,
        text=f"🔁 Now it's {game.players[opponent_id]['name']}'s turn to guess."
    )

    # Restart timer
    if game.timeout_task:
        game.timeout_task.cancel()
    game.timeout_task = asyncio.create_task(start_turn_timer(context))


async def start_turn_timer(context: ContextTypes.DEFAULT_TYPE):
    try:
        await asyncio.sleep(60)
        current_turn = game.turn
        if game.started and current_turn:
            opponent_id = game.get_opponent_id(current_turn)
            current_name = game.players[current_turn]['name']
            opponent_name = game.players[opponent_id]['name']
            await context.bot.send_message(
                chat_id=game.group_chat_id,
                text=(
                    f"⏰ Time's up! {current_name} took too long.\n"
                    f"🔁 Now it's {opponent_name}'s turn."
                )
            )
            game.turn = opponent_id
            game.timeout_task = asyncio.create_task(start_turn_timer(context))
    except asyncio.CancelledError:
        pass  # Turn changed manually — no timeout needed


async def start_private(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Hi! Use /startgame in a group to play the game.")

def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start_private))
    app.add_handler(CommandHandler("startgame", startgame))
    app.add_handler(CallbackQueryHandler(button_click))
    app.add_handler(MessageHandler(filters.TEXT & filters.ChatType.PRIVATE, handle_secret))
    app.add_handler(MessageHandler(filters.TEXT & filters.ChatType.GROUPS, handle_guess))

    print("🤖 Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
    