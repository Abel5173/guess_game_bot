import random
from typing import Dict, Optional, Tuple

class PulseCodeGame:
    """
    Core logic for the Pulse Code game.
    Manages game state, player actions, and AI opponents.
    """

    def __init__(self, host_id: int, chat_id: int, mode: str = "architect"):
        self.host_id: int = host_id
        self.chat_id: int = chat_id
        self.mode: str = mode
        self.players: Dict[int, Dict] = {}  # {user_id: {name: str, code: str, stress: int}}
        self.ai_opponents: Dict[str, Dict] = {}  # {ai_id: {name: str, code: str, stress: int}}
        self.game_started: bool = False
        self.turn_order: list = []

        # Generate a secret code for the host to start
        self._add_player(host_id, "Player 1")
        self.players[host_id]["code"] = self._generate_pulse_code()

    def _generate_pulse_code(self) -> str:
        """Generates a 4-digit secret code with no repeating digits."""
        return "".join(random.sample("0123456789", 4))

    def _add_player(self, user_id: int, name: str):
        """Adds a human player to the game."""
        if user_id not in self.players:
            self.players[user_id] = {"name": name, "code": None, "stress": 0}

    def start_game(self):
        """Initializes the game, sets up AI opponents, and defines the turn order."""
        if self.mode == "architect":
            self.ai_opponents["AI-Calculon"] = {
                "name": "Calculon",
                "code": self._generate_pulse_code(),
                "stress": 0
            }
        # Add more game modes here later
        self.game_started = True
        self.turn_order = list(self.players.keys()) + list(self.ai_opponents.keys())

    def make_guess(self, player_id: int, target_id: str, guess: str) -> Tuple[int, int, int]:
        """
        Processes a guess and returns the feedback (Hits, Flashes, Static).
        """
        if not self.game_started:
            raise ValueError("The game has not started yet.")

        if len(guess) != 4 or not guess.isdigit() or len(set(guess)) != 4:
            raise ValueError("Invalid guess format. Must be 4 unique digits.")

        target_code = self._get_target_code(target_id)
        if not target_code:
            raise ValueError("Invalid target.")

        hits = sum(1 for i in range(4) if guess[i] == target_code[i])
        flashes = sum(1 for digit in guess if digit in target_code) - hits
        static = 4 - (hits + flashes)

        # Update stress levels
        self._update_stress(player_id, static)

        return hits, flashes, static

    def _get_target_code(self, target_id: str) -> Optional[str]:
        """Retrieves the secret code for a given target (player or AI)."""
        if target_id in self.players:
            return self.players[target_id]["code"]
        if target_id in self.ai_opponents:
            return self.ai_opponents[target_id]["code"]
        return None

    def _update_stress(self, player_id: int, static_count: int):
        """Increases stress based on the number of static digits in a guess."""
        if player_id in self.players:
            self.players[player_id]["stress"] += static_count * 5  # Example stress calculation
        elif player_id in self.ai_opponents:
            self.ai_opponents[player_id]["stress"] += static_count * 5
