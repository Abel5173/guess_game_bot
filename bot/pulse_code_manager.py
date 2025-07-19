from typing import Dict, Optional, List, Union
from .pulse_code import PulseCodeGame
from bot.game.pvp import PvPGameSession
from bot.database.session_manager import save_game, load_game, delete_game, list_active_games
from bot.database.models import ActiveGame
from sqlalchemy.orm import Session
from bot.database import get_session

class PulseCodeGameManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(PulseCodeGameManager, cls).__new__(cls)
            cls._instance.games: Dict[int, PulseCodeGame] = {}
            # Load from DB
            with get_session() as session:
                for row in list_active_games(session):
                    if row.mode == 'pulse_code':
                        cls._instance.games[row.chat_id] = PulseCodeGame.from_dict(row.data)
        return cls._instance

    def get_game(self, chat_id: int) -> Optional[PulseCodeGame]:
        return self.games.get(chat_id)

    def new_game(self, chat_id: int, game: PulseCodeGame):
        self.games[chat_id] = game
        with get_session() as session:
            save_game(session, chat_id, 'pulse_code', game.to_dict())

    def end_game(self, chat_id: int):
        if chat_id in self.games:
            del self.games[chat_id]
            with get_session() as session:
                delete_game(session, chat_id)

pulse_code_game_manager = PulseCodeGameManager()

class PulseCodePvPGameManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(PulseCodePvPGameManager, cls).__new__(cls)
            cls._instance.games = {}  # chat_id: PvPGameSession
            # Load from DB
            with get_session() as session:
                for row in list_active_games(session):
                    if row.mode == 'pvp':
                        cls._instance.games[row.chat_id] = PvPGameSession.from_dict(row.data)
        return cls._instance

    def get_game(self, chat_id):
        return self.games.get(chat_id)

    def new_game(self, chat_id, player1_id):
        game = PvPGameSession(player1_id, None)
        self.games[chat_id] = game
        with get_session() as session:
            save_game(session, chat_id, 'pvp', game.to_dict())
        return game

    def join_game(self, chat_id, player2_id):
        game = self.games.get(chat_id)
        if game and game.players[1] is None:
            game.players[1] = player2_id
            game.guesses[player2_id] = []
            with get_session() as session:
                save_game(session, chat_id, 'pvp', game.to_dict())
            return True
        return False

    def end_game(self, chat_id):
        if chat_id in self.games:
            del self.games[chat_id]
            with get_session() as session:
                delete_game(session, chat_id)

pulse_code_pvp_manager = PulseCodePvPGameManager()

class PulseCodeGroupAIGame:
    """
    Represents a Group vs. AI code-breaking game session.
    Handles player management, AI setup, turn management, guessing, and win/loss logic.
    """
    def __init__(self, ai_personality: Optional[str] = None):
        self.players: List[int] = []
        self.player_states: Dict[int, Dict[str, Union[int, List[str], List[str]]]] = {}
        self.ai_personality: Optional[str] = ai_personality
        self.ai_code: Optional[str] = None
        self.turn_order: List[int] = []
        self.current_turn: int = 0
        self.active: bool = False
        self.history: List[Dict] = []
        self.winner: Optional[int] = None

    def add_player(self, user_id: int) -> None:
        """Add a player to the group game."""
        if user_id not in self.players:
            self.players.append(user_id)
            self.player_states[user_id] = {"stress": 0, "guesses": [], "penalties": []}
            self.turn_order.append(user_id)

    def set_ai(self, ai_personality: str, ai_code: str) -> None:
        """Set the AI personality and code, and activate the game."""
        self.ai_personality = ai_personality
        self.ai_code = ai_code
        self.active = True

    def get_current_player(self) -> Optional[int]:
        """Get the user ID of the current player whose turn it is."""
        if not self.turn_order:
            return None
        return self.turn_order[self.current_turn % len(self.turn_order)]

    def next_turn(self) -> None:
        """Advance to the next player's turn."""
        self.current_turn = (self.current_turn + 1) % len(self.turn_order)

    def make_guess(self, user_id: int, guess: str) -> Dict[str, Union[int, str, bool, None]]:
        """
        Process a guess from a player.
        Returns a dict with result or error.
        """
        if not self.active:
            return {"error": "Game is not active."}
        if user_id != self.get_current_player():
            return {"error": "It's not your turn."}
        if len(guess) != 4 or len(set(guess)) != 4 or not guess.isdigit():
            return {"error": "Invalid guess. Must be 4 unique digits."}
        if self.ai_code is None:
            return {"error": "AI code not set."}
        hits = sum(guess[i] == self.ai_code[i] for i in range(4))
        flashes = sum((min(guess.count(d), self.ai_code.count(d)) for d in set(guess))) - hits
        static = 4 - (hits + flashes)
        self.player_states[user_id]["guesses"].append(guess)
        self.player_states[user_id]["stress"] += static * 10
        self.player_states[user_id]["stress"] = min(self.player_states[user_id]["stress"], 100)
        penalty = None
        if self.player_states[user_id]["stress"] >= 100:
            penalty = "Failsafe Lockout"
        elif self.player_states[user_id]["stress"] >= 70:
            penalty = "System Lag"
        if penalty:
            self.player_states[user_id]["penalties"].append(penalty)
        win = hits == 4
        if win:
            self.active = False
            self.winner = user_id
        self.history.append({"guesser": user_id, "guess": guess, "hits": hits, "flashes": flashes, "static": static, "penalty": penalty, "win": win})
        return {"hits": hits, "flashes": flashes, "static": static, "stress": self.player_states[user_id]["stress"], "penalty": penalty, "win": win}

    def is_player(self, user_id: int) -> bool:
        """Check if a user is a player in the game."""
        return user_id in self.players

    def get_status(self, user_id: int) -> Optional[Dict[str, Union[int, List[str], List[str], bool]]]:
        """Get the status of a player."""
        if user_id not in self.player_states:
            return None
        state = self.player_states[user_id]
        return {
            "stress": state["stress"],
            "guesses": state["guesses"],
            "penalties": state["penalties"],
            "turn": self.get_current_player() == user_id,
        }

    def to_dict(self) -> dict:
        """Serialize the group vs. AI game state to a dictionary."""
        return {
            "players": self.players,
            "player_states": self.player_states,
            "ai_personality": self.ai_personality,
            "ai_code": self.ai_code,
            "turn_order": self.turn_order,
            "current_turn": self.current_turn,
            "active": self.active,
            "history": self.history,
            "winner": self.winner,
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'PulseCodeGroupAIGame':
        obj = cls(data.get("ai_personality"))
        obj.players = data["players"]
        obj.player_states = data["player_states"]
        obj.ai_code = data["ai_code"]
        obj.turn_order = data["turn_order"]
        obj.current_turn = data["current_turn"]
        obj.active = data["active"]
        obj.history = data["history"]
        obj.winner = data["winner"]
        return obj

class PulseCodeGroupAIGameManager:
    """Singleton manager for Group vs. AI games per chat."""
    _instance: Optional['PulseCodeGroupAIGameManager'] = None
    def __new__(cls) -> 'PulseCodeGroupAIGameManager':
        if cls._instance is None:
            cls._instance = super(PulseCodeGroupAIGameManager, cls).__new__(cls)
            cls._instance.games: Dict[int, PulseCodeGroupAIGame] = {}
            # Load from DB
            with get_session() as session:
                for row in list_active_games(session):
                    if row.mode == 'group_ai':
                        cls._instance.games[row.chat_id] = PulseCodeGroupAIGame.from_dict(row.data)
        return cls._instance
    def get_game(self, chat_id: int) -> Optional[PulseCodeGroupAIGame]:
        return self.games.get(chat_id)
    def new_game(self, chat_id: int) -> PulseCodeGroupAIGame:
        game = PulseCodeGroupAIGame()
        self.games[chat_id] = game
        with get_session() as session:
            save_game(session, chat_id, 'group_ai', game.to_dict())
        return game
    def end_game(self, chat_id: int) -> None:
        if chat_id in self.games:
            del self.games[chat_id]
            with get_session() as session:
                delete_game(session, chat_id)

class PulseCodeGroupPvPGame:
    """
    Represents a Group vs. Group code-breaking game session.
    Handles team management, code entry, turn management, guessing, and win/loss logic.
    """
    def __init__(self):
        self.teams: Dict[str, List[int]] = {"A": [], "B": []}
        self.codes: Dict[str, Optional[str]] = {"A": None, "B": None}
        self.team_states: Dict[str, Dict[int, Dict[str, Union[int, List[str], List[str]]]]] = {"A": {}, "B": {}}
        self.turn: str = "A"
        self.active: bool = False
        self.history: List[Dict] = []
        self.winner: Optional[str] = None

    def add_player(self, team: str, user_id: int) -> None:
        """Add a player to a team."""
        if user_id not in self.teams[team]:
            self.teams[team].append(user_id)
            self.team_states[team][user_id] = {"stress": 0, "guesses": [], "penalties": []}

    def set_code(self, team: str, code: str) -> bool:
        """Set and validate a team's secret code."""
        if self.codes[team] is None and len(code) == 4 and len(set(code)) == 4 and code.isdigit():
            self.codes[team] = code
            return True
        return False

    def can_start(self) -> bool:
        """Check if both teams have at least one player and a code set."""
        return all(self.codes.values()) and all(len(self.teams[t]) > 0 for t in self.teams)

    def start(self) -> None:
        """Start the game."""
        self.active = True
        self.turn = "A"

    def get_current_team(self) -> str:
        """Get the team whose turn it is."""
        return self.turn

    def next_turn(self) -> None:
        """Advance to the next team's turn."""
        self.turn = "B" if self.turn == "A" else "A"

    def make_guess(self, team: str, guess: str, user_id: int) -> Dict[str, Union[int, str, bool, None]]:
        """
        Process a guess from a team member.
        Returns a dict with result or error.
        """
        if not self.active:
            return {"error": "Game is not active."}
        if team != self.turn:
            return {"error": "It's not your team's turn."}
        if len(guess) != 4 or len(set(guess)) != 4 or not guess.isdigit():
            return {"error": "Invalid guess. Must be 4 unique digits."}
        opponent = "B" if team == "A" else "A"
        code = self.codes[opponent]
        if code is None:
            return {"error": "Opponent's code not set."}
        hits = sum(guess[i] == code[i] for i in range(4))
        flashes = sum((min(guess.count(d), code.count(d)) for d in set(guess))) - hits
        static = 4 - (hits + flashes)
        self.team_states[team][user_id]["guesses"].append(guess)
        self.team_states[team][user_id]["stress"] += static * 10
        self.team_states[team][user_id]["stress"] = min(self.team_states[team][user_id]["stress"], 100)
        penalty = None
        if self.team_states[team][user_id]["stress"] >= 100:
            penalty = "Failsafe Lockout"
        elif self.team_states[team][user_id]["stress"] >= 70:
            penalty = "System Lag"
        if penalty:
            self.team_states[team][user_id]["penalties"].append(penalty)
        win = hits == 4
        if win:
            self.active = False
            self.winner = team
        self.history.append({"team": team, "guesser": user_id, "guess": guess, "hits": hits, "flashes": flashes, "static": static, "penalty": penalty, "win": win})
        return {"hits": hits, "flashes": flashes, "static": static, "stress": self.team_states[team][user_id]["stress"], "penalty": penalty, "win": win}

    def is_player(self, user_id: int) -> bool:
        """Check if a user is a player in either team."""
        return any(user_id in self.teams[t] for t in self.teams)

    def get_status(self, team: str, user_id: int) -> Optional[Dict[str, Union[int, List[str], List[str], bool]]]:
        """Get the status of a player in a team."""
        if user_id not in self.team_states[team]:
            return None
        state = self.team_states[team][user_id]
        return {
            "stress": state["stress"],
            "guesses": state["guesses"],
            "penalties": state["penalties"],
            "turn": self.turn == team,
        }

    def to_dict(self) -> dict:
        """Serialize the group vs. group game state to a dictionary."""
        return {
            "teams": self.teams,
            "codes": self.codes,
            "team_states": self.team_states,
            "turn": self.turn,
            "active": self.active,
            "history": self.history,
            "winner": self.winner,
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'PulseCodeGroupPvPGame':
        obj = cls()
        obj.teams = data["teams"]
        obj.codes = data["codes"]
        obj.team_states = data["team_states"]
        obj.turn = data["turn"]
        obj.active = data["active"]
        obj.history = data["history"]
        obj.winner = data["winner"]
        return obj

pulse_code_group_ai_manager = PulseCodeGroupAIGameManager()

pulse_code_group_pvp_manager = PulseCodeGroupPvPGameManager()
