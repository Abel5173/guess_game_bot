from enum import Enum
from typing import Dict, List, Optional, Tuple, Union

class PvPState(Enum):
    """Enumeration for PvP game session state."""
    WAITING_FOR_CODES = 1
    IN_PROGRESS = 2
    FINISHED = 3

class PvPGameSession:
    """
    Represents a Player vs. Player (PvP) code-breaking game session.
    Handles player management, code entry, turn management, guessing, and win/loss logic.
    """
    def __init__(self, player1_id: int, player2_id: Optional[int]):
        """
        Initialize a PvP game session.
        Args:
            player1_id: The user ID of the first player.
            player2_id: The user ID of the second player (or None until joined).
        """
        self.players: List[Optional[int]] = [player1_id, player2_id]
        self.codes: Dict[int, str] = {}
        self.guesses: Dict[int, List[Tuple[str, int, int]]] = {player1_id: []}
        if player2_id is not None:
            self.guesses[player2_id] = []
        self.state: PvPState = PvPState.WAITING_FOR_CODES
        self.turn: int = 0  # 0 or 1
        self.winner: Optional[int] = None

    def set_code(self, player_id: int, code: str) -> bool:
        """
        Set and validate a player's secret code.
        Returns True if valid and set, False otherwise.
        """
        if not self._is_valid_code(code):
            return False
        self.codes[player_id] = code
        if len(self.codes) == 2:
            self.state = PvPState.IN_PROGRESS
        return True

    def current_player(self) -> Optional[int]:
        """
        Get the user ID of the current player whose turn it is.
        """
        if None in self.players:
            return None
        return self.players[self.turn % 2]

    def opponent(self) -> Optional[int]:
        """
        Get the user ID of the opponent player.
        """
        if None in self.players:
            return None
        return self.players[(self.turn + 1) % 2]

    def make_guess(self, player_id: int, guess: str) -> Dict[str, Union[str, int, bool]]:
        """
        Process a guess from a player.
        Returns a dict with result or error.
        """
        if self.state != PvPState.IN_PROGRESS:
            return {"error": "Game not in progress."}
        if player_id != self.current_player():
            return {"error": "Not your turn."}
        if not self._is_valid_code(guess):
            return {"error": "Invalid guess. Must be 4 unique digits."}
        opponent_id = self.opponent()
        if opponent_id is None or opponent_id not in self.codes:
            return {"error": "Opponent's code not set."}
        code = self.codes[opponent_id]
        exact = sum(a == b for a, b in zip(guess, code))
        misplaced = sum(min(guess.count(d), code.count(d)) for d in set(guess)) - exact
        self.guesses.setdefault(player_id, []).append((guess, exact, misplaced))
        if exact == 4:
            self.state = PvPState.FINISHED
            self.winner = player_id
            return {"win": True, "exact": exact, "misplaced": misplaced}
        self.turn += 1
        return {"win": False, "exact": exact, "misplaced": misplaced}

    def to_dict(self) -> dict:
        """Serialize the game state to a dictionary."""
        return {
            "players": self.players,
            "codes": self.codes,
            "guesses": {str(k): v for k, v in self.guesses.items()},
            "state": self.state.name,
            "turn": self.turn,
            "winner": self.winner,
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'PvPGameSession':
        """Deserialize a game state from a dictionary."""
        obj = cls(data["players"][0], data["players"][1])
        obj.codes = {int(k): v for k, v in data["codes"].items()}
        obj.guesses = {int(k): v for k, v in data["guesses"].items()}
        obj.state = PvPState[data["state"]]
        obj.turn = data["turn"]
        obj.winner = data["winner"]
        return obj

    def _is_valid_code(self, code: str) -> bool:
        """
        Validate that a code is a string of 4 unique digits.
        """
        return (
            isinstance(code, str)
            and len(code) == 4
            and code.isdigit()
            and len(set(code)) == 4
        ) 