import asyncio
from telegram.constants import ParseMode
from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes

class PhaseManager:
    """
    Handles phase transitions (task, discussion, voting) and timers for the Impostor Game.
    """
    def __init__(self, core, ai_clues_module):
        self.core = core
        self.ai_clues = ai_clues_module
        self.timeout_task = None

    async def start_task_phase(self, context: ContextTypes.DEFAULT_TYPE):
        self.core.phase = 'task'
        await context.bot.send_message(
            self.core.group_chat_id,
            "🧪 <b>Task Phase</b> begins! Crewmates, complete your tasks. Impostors, pretend to help.",
            parse_mode=ParseMode.HTML
        )
        self._cancel_timeout()
        self.timeout_task = asyncio.create_task(self._transition_to_discussion(context))

    async def _transition_to_discussion(self, context: ContextTypes.DEFAULT_TYPE):
        await asyncio.sleep(15)  # Could be configurable
        await self.start_discussion_phase(context)

    async def start_discussion_phase(self, context: ContextTypes.DEFAULT_TYPE):
        self.core.phase = 'discussion'
        self.core.discussion_history = []
        await context.bot.send_message(
            self.core.group_chat_id,
            f"🗣️ <b>Discussion Phase</b> — You have 60 seconds to talk.",
            parse_mode=ParseMode.HTML
        )
        await self.ai_clues.send_private_ai_clues(context)
        self._cancel_timeout()
        self.timeout_task = asyncio.create_task(self._transition_to_voting(context))

    async def _transition_to_voting(self, context: ContextTypes.DEFAULT_TYPE):
        await asyncio.sleep(60)  # Could be configurable
        await self.start_voting_phase(context)

    async def start_voting_phase(self, context: ContextTypes.DEFAULT_TYPE):
        self.core.phase = 'voting'
        self.core.votes.clear()
        alive_players = self.core.get_alive_players()
        buttons = [[InlineKeyboardButton(p['name'], callback_data=f"vote_{uid}")] for uid, p in alive_players.items()]
        buttons.append([InlineKeyboardButton("Skip Vote", callback_data="vote_skip")])
        markup = InlineKeyboardMarkup(buttons)
        await context.bot.send_message(
            self.core.group_chat_id,
            "🗳️ <b>Voting Phase</b> — Vote who to eject!",
            reply_markup=markup,
            parse_mode=ParseMode.HTML
        )
        self._cancel_timeout()
        # Voting resolution handled by VotingManager

    def _cancel_timeout(self):
        if self.timeout_task and not self.timeout_task.done():
            self.timeout_task.cancel() 