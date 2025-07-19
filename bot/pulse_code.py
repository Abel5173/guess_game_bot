import random
import logging
from typing import List, Dict, Optional, Tuple
from bot.llm_service import generate_ai_response, get_ai_guess

logger = logging.getLogger(__name__)


# --- AI Personalities ---
class PulseAIPersonality:
    def __init__(self, name: str, persona_prompt: str):
        self.name = name
        self.persona_prompt = persona_prompt

    def _generate_prompt(self, base_prompt: str, context: Dict) -> str:
        """Builds a detailed prompt for the LLM."""
        prompt = (
            f"You are {self.name}, a character with this persona: '{self.persona_prompt}'. "
            f"You are playing a code-breaking game called Pulse-Code. "
            f"The player's username is @{context.get('player_username', 'player')}. "
            f"Their current stress level is {context.get('stress', 0)}/100. "
            f"They just guessed `{context.get('guess', '????')}` against your code. "
            f"The result was {context.get('hits', 0)} Hits, {context.get('flashes', 0)} Flashes, and {context.get('static', 0)} Static. "
            f"This is their {len(context.get('guess_history', []))} guess. "
            f"Based on this, {base_prompt} "
            f"Keep your response concise (1-2 sentences) and in character."
        )
        return prompt

    def feedback(self, context: Dict) -> str:
        """Generates AI feedback using the LLM."""
        base_prompt = "provide direct feedback to the player about their guess."
        prompt = self._generate_prompt(base_prompt, context)
        return generate_ai_response(prompt)

    def get_hint(self, context: Dict) -> str:
        """Generates a hint using the LLM."""
        base_prompt = "provide a cryptic hint to the player. Do not reveal the code."
        prompt = self._generate_prompt(base_prompt, context)
        return generate_ai_response(prompt)

    def public_banter(self, context: Dict) -> str:
        """Generates public banter using the LLM."""
        base_prompt = "generate a witty or taunting remark to say to the player in a public chat."
        prompt = self._generate_prompt(base_prompt, context)
        return generate_ai_response(prompt)


# --- Core Game Logic ---
def generate_pulse_code() -> str:
    digits = random.sample("0123456789", 4)
    return "".join(digits)


def analyze_guess(guess: str, code: str) -> Tuple[int, int, int]:
    hits = sum(guess[i] == code[i] for i in range(4))
    flashes = sum((min(guess.count(d), code.count(d)) for d in set(guess))) - hits
    static = 4 - (hits + flashes)
    return hits, flashes, static


class PulsePlayerState:
    def __init__(
        self,
        user_id: int,
        code: Optional[str] = None,
        ai_personality: Optional[str] = None,
    ):
        self.user_id = user_id
        self.code = code or generate_pulse_code()
        self.stress = 0  # 0-100
        self.ai_personality = ai_personality
        self.is_ai = ai_personality is not None
        self.guesses: List[str] = []
        self.hints_used = 0
        self.gambit_used = False
        self.mind_link_used = False

    def increase_stress(self, static: int):
        self.stress += static * 10
        self.stress = min(self.stress, 100)

    def apply_penalty(self):
        if self.stress >= 100:
            return "Failsafe Lockout"
        elif self.stress >= 70:
            return random.choice(["Data Glitch", "System Lag"])
        return None


class PulseCodeGame:
    def __init__(
        self,
        mode: str,
        players: List[int],
        ai_personalities: Optional[List[str]] = None,
    ):
        self.mode = mode
        self.players: Dict[int, PulsePlayerState] = {}
        self.turn_order: List[int] = []
        self.active = True
        self.history: List[Dict] = []
        self.current_turn = 0
        self.winner: Optional[int] = None
        self.ai_personalities = ai_personalities or []
        self.init_players(players)
        self.ai_targets: Dict[int, int] = {}

    def init_players(self, players: List[int]):
        for idx, user_id in enumerate(players):
            ai_personality = (
                self.ai_personalities[idx] if idx < len(self.ai_personalities) else None
            )
            self.players[user_id] = PulsePlayerState(
                user_id, ai_personality=ai_personality
            )
            self.turn_order.append(user_id)

    def get_current_player(self) -> PulsePlayerState:
        return self.players[self.turn_order[self.current_turn % len(self.turn_order)]]

    def next_turn(self):
        self.current_turn = (self.current_turn + 1) % len(self.turn_order)

    def make_guess(self, guesser_id: int, target_id: int, guess: str, guesser_username: str) -> Dict:
        if not self.active:
            return {"error": "Game is not active."}
        guesser = self.players[guesser_id]
        target = self.players[target_id]
        if guesser.stress >= 100:
            return {"error": "System Stress is critical! You cannot guess."}
        if len(guess) != 4 or len(set(guess)) != 4 or not guess.isdigit():
            return {"error": "Invalid guess. Must be 4 unique digits."}
        
        hits, flashes, static = analyze_guess(guess, target.code)
        guesser.guesses.append(guess)
        guesser.increase_stress(static)
        penalty = guesser.apply_penalty()
        
        ai_feedback = None
        ai_public = None

        if target.is_ai and target.ai_personality:
            ai_persona_key = target.ai_personality.lower()
            ai = AI_PERSONALITIES.get(ai_persona_key)
            if ai:
                context = {
                    "player_username": guesser_username,
                    "guess": guess,
                    "hits": hits,
                    "flashes": flashes,
                    "static": static,
                    "stress": guesser.stress,
                    "guess_history": guesser.guesses,
                }
                ai_feedback = ai.feedback(context)
                if random.random() < 0.3:  # 30% chance for public banter
                    ai_public = ai.public_banter(context)

        result = {
            "hits": hits,
            "flashes": flashes,
            "static": static,
            "stress": guesser.stress,
            "penalty": penalty,
            "win": hits == 4,
            "ai_feedback": ai_feedback,
            "ai_public": ai_public,
        }
        
        if hits == 4:
            self.active = False
            self.winner = guesser_id
            
        self.history.append(
            {"guesser": guesser_id, "target": target_id, "guess": guess, "result": result}
        )
        return result

    def get_status(self, user_id: int) -> Dict:
        player = self.players[user_id]
        return {
            "stress": player.stress,
            "guesses": player.guesses,
            "hints_used": player.hints_used,
            "gambit_used": player.gambit_used,
            "mind_link_used": player.mind_link_used,
        }

    def ai_make_guess(self, guesser_id: int, target_id: int) -> Dict:
        if not self.active:
            return {"error": "Game is not active."}
        guesser = self.players[guesser_id]
        target = self.players[target_id]

        # AI generates a guess based on its history (if any)
        ai_history = [
            {"guess": h["guess"], "hits": h["result"]["hits"], "flashes": h["result"]["flashes"]}
            for h in self.history
            if h["guesser"] == guesser_id
        ]
        ai_guess = get_ai_guess(ai_history)

        if len(ai_guess) != 4 or len(set(ai_guess)) != 4 or not ai_guess.isdigit():
            logger.warning(f"AI generated an invalid guess: {ai_guess}. Generating a random valid guess.")
            ai_guess = generate_pulse_code() # Fallback to a valid random guess

        hits, flashes, static = analyze_guess(ai_guess, target.code)
        guesser.guesses.append(ai_guess)
        guesser.increase_stress(static)
        penalty = guesser.apply_penalty()

        result = {
            "guess": ai_guess,
            "hits": hits,
            "flashes": flashes,
            "static": static,
            "stress": guesser.stress,
            "penalty": penalty,
            "win": hits == 4,
        }

        if hits == 4:
            self.active = False
            self.winner = guesser_id

        self.history.append(
            {"guesser": guesser_id, "target": target_id, "guess": ai_guess, "result": result}
        )
        return result

    @classmethod
    def setup_architect(cls, player_id: int, ai_personality: str) -> "PulseCodeGame":
        ai_id = -1
        players = [player_id, ai_id]
        ai_personalities = [None, ai_personality] # Player has no AI personality, AI has one
        game = cls(mode="architect", players=players, ai_personalities=ai_personalities)
        # In architect mode, player guesses AI's code, and AI guesses player's code
        game.turn_order = [player_id, ai_id] # Player goes first, then AI
        game.ai_targets = {player_id: ai_id, ai_id: player_id} # Player targets AI, AI targets Player
        return game

AI_PERSONALITIES = {
    "calculon": PulseAIPersonality(
        "Calculon",
        "You are a cold, calculating robot. You speak in a formal, logical manner and often reference probabilities and efficiency.",
    ),
    "maverick": PulseAIPersonality(
        "Maverick",
        "You are a hot-shot pilot, full of bravado and confidence. You use slang, are a bit of a show-off, and enjoy taunting your opponents.",
    ),
    "sentinel": PulseAIPersonality(
        "Sentinel",
        "You are a mysterious, ancient guardian of a forgotten system. Your words are cryptic, wise, and often hint at a deeper, unseen reality.",
    ),
}