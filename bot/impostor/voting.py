from telegram.ext import ContextTypes
from telegram.constants import ParseMode
from typing import Dict, Optional, Tuple, Any


class VotingManager:
    """
    Handles voting logic, anonymous voting, and vote resolution for the Impostor Game.
    """

    def __init__(self, core: Any) -> None:
        self.core = core

    def vote(self, voter_id: int, target_id: int) -> bool:
        if (
            voter_id in self.core.players
            and target_id in self.core.players
            and self.core.players[voter_id]["alive"]
        ):
            self.core.votes[voter_id] = target_id
            return True
        return False

    def resolve_votes(self) -> Tuple[Optional[int], str]:
        counts: Dict[int, int] = {}
        for target in self.core.votes.values():
            if target is not None:
                counts[target] = counts.get(target, 0) + 1
        if not counts:
            return None, "No one was ejected."
        max_votes = max(counts.values())
        candidates = [uid for uid, v in counts.items() if v == max_votes]
        if len(candidates) > 1:
            return None, "It's a tie! No one was ejected."
        voted_out = candidates[0]
        self.core.players[voted_out]["alive"] = False
        self.core.votes.clear()
        return (
            voted_out,
            f"{
            self.core.players[voted_out]['name']} was ejected!",
        )

    async def handle_vote(
        self, update: Any, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        query = update.callback_query
        await query.answer()
        user_id = query.from_user.id
        if (
            self.core.phase != "voting"
            or user_id not in self.core.players
            or not self.core.players[user_id]["alive"]
        ):
            await query.message.reply_text("⛔ You can't vote now!")
            return
        if query.data == "vote_skip":
            self.core.votes[user_id] = None
            await query.message.reply_text(
                f"✅ {self.core.players[user_id]['name']} skipped their vote."
            )
        elif query.data.startswith("vote_"):
            target_id = int(query.data.replace("vote_", ""))
            if target_id in self.core.players and self.core.players[target_id]["alive"]:
                self.core.votes[user_id] = target_id
                if self.core.config.get("anonymous_voting", True):
                    await query.message.reply_text("✅ Vote recorded.")
                else:
                    await query.message.reply_text(
                        f"✅ {self.core.players[user_id]['name']} voted for {self.core.players[target_id]['name']}."
                    )
            else:
                await query.message.reply_text("❌ Invalid vote.")
        alive_players = self.core.get_alive_players()
        if len(self.core.votes) >= len(alive_players):
            # Optionally, signal to resolve votes immediately here
            pass

    async def start_voting(self, context: ContextTypes.DEFAULT_TYPE) -> None:
        markup = self.core.get_voting_markup()
        await context.bot.send_message(
            self.core.group_chat_id,
            "🗳️ <b>Voting Phase</b> — Vote who to eject!",
            reply_markup=markup,
            parse_mode=ParseMode.HTML,
        )
