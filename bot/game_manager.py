import logging
from bot.pulse_code import PulseCodeGame

logger = logging.getLogger(__name__)


class GameManager:
    def __init__(self):
        self.impostor_games = {}  # chat_id: ImpostorGame
        self.guess_games = {}  # chat_id: GuessGame (to be implemented)
        self.pulse_code_games = {}  # chat_id: PulseCodeGame
        self.pulse_code_players = {}  # chat_id: set of user_ids

    def get_pulse_code_game(self, chat_id):
        return self.pulse_code_games.get(chat_id)

    def start_pulse_code_game(self, chat_id, mode, players, ai_personalities=None):
        game = PulseCodeGame(mode, players, ai_personalities)
        self.pulse_code_games[chat_id] = game
        self.pulse_code_players[chat_id] = set(players)
        logger.info(f"Started Pulse Code game in chat {chat_id} with mode {mode}")
        return game

    def end_pulse_code_game(self, chat_id):
        if chat_id in self.pulse_code_games:
            del self.pulse_code_games[chat_id]
            logger.info(f"Ended Pulse Code game in chat {chat_id}")
        if chat_id in self.pulse_code_players:
            del self.pulse_code_players[chat_id]

    def join_pulse_code(self, chat_id, user_id):
        if chat_id not in self.pulse_code_players:
            self.pulse_code_players[chat_id] = set()
        self.pulse_code_players[chat_id].add(user_id)
        logger.info(f"User {user_id} joined Pulse Code in chat {chat_id}")

    def leave_pulse_code(self, chat_id, user_id):
        if chat_id in self.pulse_code_players:
            self.pulse_code_players[chat_id].discard(user_id)
            logger.info(f"User {user_id} left Pulse Code in chat {chat_id}")
            # If no players left, clean up session
            if not self.pulse_code_players[chat_id]:
                self.end_pulse_code_game(chat_id)

    def list_pulse_code_players(self, chat_id):
        return list(self.pulse_code_players.get(chat_id, []))


# Global instance
manager = GameManager()
