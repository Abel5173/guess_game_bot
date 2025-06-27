from bot.utils import query_ai

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
                history = "\n".join(self.core.discussion_history[-3:]) or "Not much was said."
                if p['role'] == 'crewmate':
                    prompt = (
                        f"You are playing a social deduction game. One of the following players is the impostor: "
                        f"{', '.join([pl['name'] for pid, pl in self.core.get_alive_players().items() if pid != uid])}.\n"
                        f"Here's the latest group discussion: {history}.\n"
                        "Give a vague but helpful clue about who might be the impostor. Be subtle and mysterious."
                    )
                else:
                    prompt = (
                        f"You're an impostor in a game. Here is the recent group discussion: {history}.\n"
                        "Give a misleading clue to confuse crewmates. Include metaphors, riddles, or vague language."
                    )
                clue = await query_ai(prompt)
                await context.bot.send_message(uid, f"🤖 AI Clue: {clue}")
            except Exception:
                pass 