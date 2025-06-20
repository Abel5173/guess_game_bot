from bot.guess_game import GuessGame
from bot.impostor_game import ImpostorGame

class GameManager:
    def __init__(self):
        self.current_game = None
        self.current_type = None

    def set_game(self, game_type):
        if game_type == "guess":
            self.current_game = GuessGame()
            self.current_type = "guess"
        elif game_type == "impostor":
            self.current_game = ImpostorGame()
            self.current_type = "impostor"
        else:
            self.current_game = None
            self.current_type = None

    def get_game(self):
        return self.current_game

    def get_type(self):
        return self.current_type 