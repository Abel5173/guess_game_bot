import os
import requests
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import ContextTypes
from dotenv import load_dotenv
from bot.utils import query_ai

class GuessGame:
    def __init__(self):
        self.players = {}
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
        return next((uid for uid in self.players if uid != user_id), None)

    def score_guess(self, guess, target):
        N = sum(1 for digit in guess if digit in target)
        O = sum(1 for g, t in zip(guess, target) if g == t)
        return N, O

    def reset(self):
        # Cancel any running timeout task and clear all state
        if self.timeout_task:
            try:
                self.timeout_task.cancel()
            except Exception:
                pass
        self.players = {}
        self.group_chat_id = None
        self.started = False
        self.turn = None
        self.guess_counts = {}
        self.timeout_task = None

    # Handlers
    async def startgame(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        msg = update.message or (update.callback_query and update.callback_query.message)
        if not msg:
            return
        chat = update.effective_chat
        if chat.type not in ["group", "supergroup"]:
            return await msg.reply_text("⚠️ Use /startgame in a group.")
        self.reset()
        self.group_chat_id = chat.id
        markup = InlineKeyboardMarkup([
            [InlineKeyboardButton("🎮 Join Game", callback_data="join_guess")],
            [InlineKeyboardButton("📜 How to Play", callback_data="show_guess_rules")],
        ])
        await msg.reply_text(
            "👾 <b>Welcome to Smart Guess Game!</b>\n\nChallenge your friends and test your mind! Ready to play?",
            reply_markup=markup,
            parse_mode=ParseMode.HTML
        )

    async def button_click(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        user = query.from_user
        if query.data == "join_guess":
            if self.add_player(user.id, user.first_name):
                try:
                    await context.bot.send_message(
                        user.id,
                        f"🔒 <b>Welcome, {user.first_name}!</b>\n\nPlease send me your <b>secret 4-digit number</b>.\nThis will be your code for the game! 🤫",
                        parse_mode=ParseMode.HTML
                    )
                    await query.message.reply_text(
                        f"🎉 <b>{user.first_name}</b> joined the game!\nWaiting for another player... 👀",
                        parse_mode=ParseMode.HTML
                    )
                except Exception:
                    bot_username = (await context.bot.get_me()).username
                    await query.message.reply_text(
                        f"⚠️ <b>{user.first_name}</b>, please start a private chat with me first:\n"
                        f"<a href='https://t.me/{bot_username}'>Click here to chat</a> and press <b>Start</b>, then join the game again!",
                        parse_mode=ParseMode.HTML,
                        disable_web_page_preview=True
                    )
                    self.players.pop(user.id, None)
                    self.guess_counts.pop(user.id, None)
            else:
                await query.message.reply_text(
                    "⚠️ <b>Already joined or game full.</b>",
                    parse_mode=ParseMode.HTML
                )
        elif query.data == "show_guess_rules":
            await query.message.reply_text(
                "📜 <b>How to Play Smart Guess Game</b>\n\n"
                "1️⃣ Each player picks a <b>secret 4-digit number</b>.\n"
                "2️⃣ Take turns guessing your opponent's number.\n"
                "3️⃣ The bot gives feedback:\n"
                "   • <b>N</b> = correct digits (any position)\n"
                "   • <b>O</b> = correct digits in the right position\n"
                "4️⃣ After 3 tries, the AI will help you with hints!\n"
                "🏆 First to guess wins!\n\n"
                "Ready to play? Click <b>Join Game</b> below!",
                parse_mode=ParseMode.HTML
            )

    async def handle_secret(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        text = update.message.text.strip()
        if update.message.chat.type != 'private':
            return
        if user.id in self.players and not self.players[user.id]['ready']:
            if text.isdigit() and len(text) == 4:
                self.set_secret(user.id, text)
                await update.message.reply_text("✅ Secret set!")
                if self.is_ready():
                    ids = list(self.players)
                    self.turn = ids[0]
                    p1, p2 = self.players[ids[0]]['name'], self.players[ids[1]]['name']
                    await context.bot.send_message(
                        self.group_chat_id,
                        f"🔥 Game started between {p1} and {p2}!\n🎯 {p1} goes first."
                    )
                    self.started = True
                    self.timeout_task = asyncio.create_task(self.start_turn_timer(context))
            else:
                await update.message.reply_text("❌ Must be a 4-digit number.")

    async def handle_guess(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        uid = user.id
        text = update.message.text.strip()
        if not self.started or update.message.chat_id != self.group_chat_id:
            return
        if uid != self.turn or uid not in self.players:
            return await update.message.reply_text("⛔ Not your turn!")
        if not text.isdigit() or len(text) != 4:
            return await update.message.reply_text("❗ Use a valid 4-digit number.")
        opponent_id = self.get_opponent_id(uid)
        opponent_secret = self.players[opponent_id]['secret']
        N, O = self.score_guess(text, opponent_secret)
        self.guess_counts[uid] += 1
        count = self.guess_counts[uid]
        await update.message.reply_text(
            f"🎯 <b>You guessed:</b> <code>{text}</code>\n"
            f"🟢 <b>N</b>: {N}   🟡 <b>O</b>: {O}\n"
            f"({count} tries so far)",
            parse_mode=ParseMode.HTML
        )
        # Use AI safely and handle errors
        ai_prompt = f"A player guessed {text} and got N={N}, O={O}. Give a 1-sentence hint or fun response."
        try:
            ai_reply = await query_ai(ai_prompt)
        except Exception:
            ai_reply = "🤖 AI is unavailable right now."
        await context.bot.send_message(self.group_chat_id, f"🤖 {ai_reply}")
        if text == opponent_secret:
            await context.bot.send_message(self.group_chat_id, f"🏆 {user.first_name} WINS! 🎉 Guessed in {count} tries.")
            return self.reset()
        self.turn = opponent_id
        await context.bot.send_message(
            self.group_chat_id,
            f"🔁 Now it's {self.players[opponent_id]['name']}'s turn."
        )
        if self.timeout_task:
            try:
                self.timeout_task.cancel()
            except Exception:
                pass
        self.timeout_task = asyncio.create_task(self.start_turn_timer(context))

    async def start_turn_timer(self, context: ContextTypes.DEFAULT_TYPE):
        try:
            await asyncio.sleep(60)
            if self.started:
                current = self.turn
                next_turn = self.get_opponent_id(current)
                self.turn = next_turn
                name = self.players[next_turn]['name']
                await context.bot.send_message(self.group_chat_id, f"⏰ Turn timeout! {name}, it's your turn now.")
                self.timeout_task = asyncio.create_task(self.start_turn_timer(context))
        except asyncio.CancelledError:
            pass 