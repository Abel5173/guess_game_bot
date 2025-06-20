import random
import asyncio
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.constants import ParseMode
from telegram.ext import ContextTypes
from bot.utils import generate_clue

class ImpostorGame:
    def __init__(self):
        self.players = {}  # user_id: {name, role, alive}
        self.group_chat_id = None
        self.started = False
        self.impostors = set()
        self.votes = {}
        self.phase = 'waiting'

    def add_player(self, user_id, name):
        if self.started or user_id in self.players:
            return False
        self.players[user_id] = {'name': name, 'role': 'crewmate', 'alive': True}
        return True

    def start_game(self):
        if len(self.players) < 4:
            return False
        self.started = True
        self.phase = 'discussion'
        # Randomly assign 1 impostor
        impostor_id = random.choice(list(self.players.keys()))
        self.players[impostor_id]['role'] = 'impostor'
        self.impostors.add(impostor_id)
        return True

    def get_alive_players(self):
        return {uid: p for uid, p in self.players.items() if p['alive']}

    def vote(self, voter_id, target_id):
        if voter_id in self.players and target_id in self.players and self.players[voter_id]['alive']:
            self.votes[voter_id] = target_id
            return True
        return False

    def resolve_votes(self):
        counts = {}
        for target in self.votes.values():
            counts[target] = counts.get(target, 0) + 1
        if not counts:
            return None, "No one was ejected."
        # Handle ties
        max_votes = max(counts.values())
        candidates = [uid for uid, v in counts.items() if v == max_votes]
        if len(candidates) > 1:
            return None, "It's a tie! No one was ejected."
        voted_out = candidates[0]
        self.players[voted_out]['alive'] = False
        self.votes.clear()
        return voted_out, f"{self.players[voted_out]['name']} was ejected!"

    def check_game_over(self):
        alive = self.get_alive_players()
        impostors_alive = sum(1 for p in alive.values() if p['role'] == 'impostor')
        crewmates_alive = len(alive) - impostors_alive
        if impostors_alive == 0:
            return True, "🎉 Crewmates win!"
        if impostors_alive >= crewmates_alive:
            return True, "💀 Impostor wins!"
        return False, ""

    # Handler functions
    async def join_impostor(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        if self.add_player(user.id, user.first_name):
            await update.message.reply_text(f"✅ {user.first_name} joined the game.")
        else:
            await update.message.reply_text("⚠️ You are already in the game or the game has started.")

    async def start_impostor_game(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        self.group_chat_id = update.effective_chat.id
        if not self.start_game():
            await update.message.reply_text("❗ Need at least 4 players to start.")
            return
        names = [p['name'] for p in self.players.values()]
        for uid, p in self.players.items():
            try:
                await context.bot.send_message(uid, f"🎭 You are a <b>{p['role']}</b>.", parse_mode=ParseMode.HTML)
            except Exception:
                pass  # Ignore if bot can't message user
        # Generate AI clue with error handling
        try:
            clue = await generate_clue(names)
        except Exception:
            clue = "🤖 AI is unavailable right now."
        await context.bot.send_message(self.group_chat_id, f"🕵️ Mysterious AI says: {clue}") 