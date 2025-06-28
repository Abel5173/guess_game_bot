from bot.utils import query_ai
from telegram import ParseMode


class AIClueManager:
    """
    Handles AI clue generation and private clue delivery for the Impostor Game.
    """

    def __init__(self, core):
        self.core = core

    async def send_private_ai_clues(self, context):
        for uid, p in self.core.players.items():
            if not p['alive']:
                continue
            try:
                history = "\n".join(
                    self.core.discussion_history[-3:]) or "Not much was said."
                if p['role'] == 'crewmate':
                    prompt = (
                        f"Players: {', '.join([pl['name'] for pid, pl in self.core.get_alive_players().items() if pid != uid])}\n"
                        f"Discussion: {history}\n"
                        "Give a subtle clue for the crewmates."
                    )
                else:
                    prompt = (
                        f"You're an impostor in a game. Here is the recent group discussion: {history}.\n"
                        "Give a misleading clue to confuse crewmates. Include metaphors, riddles, or vague language."
                    )
                clue = await query_ai(prompt)
                await context.bot.send_message(
                    uid,
                    f"🤖 <b>AI Clue</b> for {p['name']}\n\n{clue}",
                    parse_mode=ParseMode.HTML
                )
            except Exception:
                pass
