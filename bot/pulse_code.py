import random
import logging
from typing import List, Dict, Optional, Tuple

logger = logging.getLogger(__name__)


# --- AI Personalities ---
class PulseAIPersonality:
    def __init__(self, name: str):
        self.name = name

    def feedback(self, guess: str, code: str) -> str:
        # Default feedback, can be overridden
        return "Processing your guess..."

    def get_hint(self, code: str) -> str:
        # Default hint, can be overridden
        return "No hint available."


class Calculon(PulseAIPersonality):
    def feedback(
        self,
        guess: str,
        code: str,
        hits: int,
        flashes: int,
        static: int,
        stress: int,
        guess_history: list,
    ) -> str:
        msg = f"[Calculon] Analysis: {hits} Hits, {flashes} Flashes, {static} Static."
        if guess in guess_history[:-1]:
            msg += " You have repeated a previous guess. Redundant input detected."
        if hits == 4:
            msg += " Solution confirmed. You have achieved optimal deduction."
        elif stress > 80:
            msg += " Your logic is faltering under pressure."
        elif static == 4:
            msg += " None of your digits are present. Recalibrate your approach."
        elif hits == 0 and flashes == 0:
            msg += " No progress. Consider a new hypothesis."
        else:
            msg += " Continue refining your hypothesis."
        return msg

    def get_hint(self, code: str, guess_history: list) -> str:
        return "The code is logically constructed. Consider digit progression."

    def public_banter(self, player_username: str, stress: int) -> str:
        if stress > 90:
            return f"[Calculon] @${player_username}, your system is on the verge of collapse."
        return random.choice(
            [
                f"[Calculon] @${player_username}, your deduction rate is suboptimal.",
                f"[Calculon] @${player_username}, are you certain of your logic?",
            ]
        )


class Maverick(PulseAIPersonality):
    def feedback(
        self,
        guess: str,
        code: str,
        hits: int,
        flashes: int,
        static: int,
        stress: int,
        guess_history: list,
    ) -> str:
        msg = f"[Maverick] {hits} Hits, {flashes} Flashes, {static} Static."
        if guess in guess_history[:-1]:
            msg += " Deja vu? Try something new!"
        if hits == 4:
            msg += " Whoa! You actually did it!"
        elif stress > 80:
            msg += " Feeling the heat? Maybe try something wild!"
        elif static == 4:
            msg += " Swing and a miss! Not even close."
        elif hits == 0 and flashes == 0:
            msg += " Ouch, that's cold."
        else:
            msg += " Not bad, but can you keep up with me?"
        return msg

    def get_hint(self, code: str, guess_history: list) -> str:
        return "I like codes with a twist. Maybe the answer isn't what you expect."

    def public_banter(self, player_username: str, stress: int) -> str:
        if stress > 90:
            return f"[Maverick] @${player_username}, are you about to break?"
        return random.choice(
            [
                f"[Maverick] @${player_username}, you call that a guess?",
                f"[Maverick] @${player_username}, try to keep up!",
            ]
        )


class Sentinel(PulseAIPersonality):
    def feedback(
        self,
        guess: str,
        code: str,
        hits: int,
        flashes: int,
        static: int,
        stress: int,
        guess_history: list,
    ) -> str:
        msg = f"[Sentinel] {hits} Hits, {flashes} Flashes, {static} Static."
        if guess in guess_history[:-1]:
            msg += " Pattern repetition detected."
        if hits == 4:
            msg += " The system acknowledges your mastery."
        elif stress > 80:
            msg += " Warning: Your system is nearing collapse."
        elif static == 4:
            msg += " All signals lost. None of your guess is present."
        elif hits == 0 and flashes == 0:
            msg += " The void grows deeper."
        else:
            msg += " The system observes. Adjust your tactics."
        return msg

    def get_hint(self, code: str, guess_history: list) -> str:
        return "Peripheral digits may be more important than you think."

    def public_banter(self, player_username: str, stress: int) -> str:
        if stress > 90:
            return f"[Sentinel] @${player_username}, system integrity is critical."
        return random.choice(
            [
                f"[Sentinel] @${player_username}, the system is watching.",
                f"[Sentinel] @${player_username}, your approach is being logged.",
            ]
        )


AI_PERSONALITIES = {
    "calculon": Calculon("Calculon"),
    "maverick": Maverick("Maverick"),
    "sentinel": Sentinel("Sentinel"),
}


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
        # More static = more stress
        self.stress += static * 10
        self.stress = min(self.stress, 100)

    def apply_penalty(self):
        # Apply penalty based on stress
        if self.stress >= 100:
            return "Failsafe Lockout"
        elif self.stress >= 70:
            return random.choice(["Data Glitch", "System Lag"])
        elif self.stress >= 40:
            return "Warning: System Stress Rising"
        return None


class PulseCodeGame:
    def __init__(
        self,
        mode: str,
        players: List[int],
        ai_personalities: Optional[List[str]] = None,
    ):
        self.mode = mode  # architect, dual, triple
        self.players: Dict[int, PulsePlayerState] = {}
        self.turn_order: List[int] = []
        self.active = True
        self.history: List[Dict] = []
        self.current_turn = 0
        self.winner: Optional[int] = None
        self.ai_personalities = ai_personalities or []
        self.init_players(players)
        self.last_guess_target: Optional[int] = None  # For feedback in triple threat

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

    def make_guess(self, guesser_id: int, target_id: int, guess: str) -> Dict:
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
            ai = AI_PERSONALITIES.get(target.ai_personality.lower())
            if ai:
                ai_feedback = ai.feedback(
                    guess,
                    target.code,
                    hits,
                    flashes,
                    static,
                    guesser.stress,
                    guesser.guesses,
                )
                # Occasionally send public banter
                if random.random() < 0.25 or (
                    guesser.stress > 90 and random.random() < 0.5
                ):
                    ai_public = ai.public_banter(
                        getattr(guesser, "username", str(guesser_id)), guesser.stress
                    )
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
            {
                "guesser": guesser_id,
                "target": target_id,
                "guess": guess,
                "result": result,
            }
        )
        self.last_guess_target = target_id
        return result

    def use_mind_link(self, user_id: int, target_id: int) -> str:
        player = self.players[user_id]
        if player.mind_link_used:
            return "Mind Link already used."
        player.mind_link_used = True
        code = self.players[target_id].code
        hint = f"One of the digits is {random.choice(code)}."
        player.increase_stress(5)
        return hint

    def desperation_gambit(self, user_id: int, target_id: int, guess: str) -> Dict:
        player = self.players[user_id]
        if player.stress < 80:
            return {"error": "Desperation Gambit only available at high stress!"}
        if player.gambit_used:
            return {"error": "Desperation Gambit already used."}
        player.gambit_used = True
        hits, flashes, static = analyze_guess(guess, self.players[target_id].code)
        if hits == 4:
            self.active = False
            self.winner = user_id
            return {"result": "Gambit Success! You win!", "win": True}
        else:
            player.stress = 100
            self.active = False
            return {"result": "System Collapse! You lose.", "win": False}

    def get_status(self, user_id: int) -> Dict:
        player = self.players[user_id]
        return {
            "stress": player.stress,
            "guesses": player.guesses,
            "hints_used": player.hints_used,
            "gambit_used": player.gambit_used,
            "mind_link_used": player.mind_link_used,
        }

    # --- Dual Operative Mode ---
    @classmethod
    def setup_dual_operative(cls, player1_id: int, player2_id: int) -> "PulseCodeGame":
        # Each player faces a different AI
        ai1_id = -101
        ai2_id = -102
        players = [player1_id, ai1_id, player2_id, ai2_id]
        ai_personalities = [None, "calculon", None, "maverick"]
        game = cls(mode="dual", players=players, ai_personalities=ai_personalities)
        game.turn_order = [player1_id, player2_id]  # Only humans take turns
        game.ai_targets = {player1_id: ai1_id, player2_id: ai2_id}
        return game

    # --- Triple Threat Mode ---
    @classmethod
    def setup_triple_threat(cls, player1_id: int, player2_id: int) -> "PulseCodeGame":
        ai_id = -201
        players = [player1_id, player2_id, ai_id]
        ai_personalities = [None, None, "sentinel"]
        game = cls(mode="triple", players=players, ai_personalities=ai_personalities)
        game.turn_order = [player1_id, player2_id, ai_id]
        return game

    def is_ai(self, user_id: int) -> bool:
        return self.players[user_id].is_ai

    def get_ai_targets(self) -> Dict[int, int]:
        # Only for dual mode
        return getattr(self, "ai_targets", {})

    def get_last_guess_target(self) -> Optional[int]:
        return self.last_guess_target
