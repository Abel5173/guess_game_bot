from typing import Dict, Optional
from bot.impostor import ImpostorGame
from bot.pulse_code import PulseCodeGame

class GameManager:
    def __init__(self):
        self.games: Dict[int, object] = {}
        self.game_types: Dict[int, str] = {}

    def start_new_game(self, chat_id: int, game_type: str, host_id: int):
        if chat_id in self.games:
            return "A game is already in progress in this chat."

        if game_type == "impostor":
            self.games[chat_id] = ImpostorGame()
            self.game_types[chat_id] = "impostor"
            return "impostor_started"
        elif game_type == "pulse_code":
            self.games[chat_id] = PulseCodeGame(host_id=host_id, chat_id=chat_id)
            self.game_types[chat_id] = "pulse_code"
            return "pulse_code_started"
        else:
            return "Unknown game type."

    def get_game(self, chat_id: int) -> Optional[object]:
        return self.games.get(chat_id)

    def get_game_type(self, chat_id: int) -> Optional[str]:
        return self.game_types.get(chat_id)

    def end_game(self, chat_id: int):
        if chat_id in self.games:
            del self.games[chat_id]
            del self.game_types[chat_id]

# Global instance of the game manager
game_manager = GameManager()
