import random
from typing import Dict, List, Optional, Tuple

class PulseCodeCore:
    def __init__(self, config: Optional[dict] = None):
        self.config = config or {
            "code_length": 4,
            "min_digit": 0,
            "max_digit": 9,
        }
        self.players: Dict[int, Dict] = {}
        self.ai_opponents: Dict[str, Dict] = {}
        self.game_mode: Optional[str] = None
        self.game_log: List[str] = []

    def generate_pulse_code(self) -> List[int]:
        digits = list(range(self.config["min_digit"], self.config["max_digit"] + 1))
        return random.sample(digits, self.config["code_length"])

    def add_player(self, user_id: int, name: str):
        if user_id not in self.players:
            self.players[user_id] = {
                "name": name,
                "pulse_code": self.generate_pulse_code(),
                "system_stress": 0,
                "mind_link_available": True,
            }

    def add_ai_opponent(self, ai_id: str, personality: str):
        if ai_id not in self.ai_opponents:
            self.ai_opponents[ai_id] = {
                "personality": personality,
                "pulse_code": self.generate_pulse_code(),
                "system_stress": 0,
            }

    def make_guess(self, guesser_id: int, target_id: int, guess_code: List[int]) -> Tuple[int, int, int]:
        target_code = []
        if target_id in self.players:
            target_code = self.players[target_id]["pulse_code"]
        elif str(target_id) in self.ai_opponents:
            target_code = self.ai_opponents[str(target_id)]["pulse_code"]
        else:
            raise ValueError("Invalid target ID")

        hits = sum(1 for g, t in zip(guess_code, target_code) if g == t)
        flashes = len(set(guess_code) & set(target_code)) - hits
        static = self.config["code_length"] - (hits + flashes)

        # Update system stress
        stress_increase = static * 5 + flashes * 2
        if guesser_id in self.players:
            self.players[guesser_id]["system_stress"] += stress_increase
        elif str(guesser_id) in self.ai_opponents:
            self.ai_opponents[str(guesser_id)]["system_stress"] += stress_increase

        return hits, flashes, static
