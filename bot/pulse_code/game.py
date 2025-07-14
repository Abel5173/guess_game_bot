from .core import PulseCodeCore

class PulseCodeGame:
    def __init__(self, config=None):
        self.core = PulseCodeCore(config)

    def start_architect_game(self, user_id: int, user_name: str):
        self.core.game_mode = "architect"
        self.core.add_player(user_id, user_name)
        self.core.add_ai_opponent("PulseCodeBot", "The Calculon")

    def start_dual_operative_game(self, player1_id: int, player1_name: str, player2_id: int, player2_name: str):
        self.core.game_mode = "dual_operative"
        self.core.add_player(player1_id, player1_name)
        self.core.add_player(player2_id, player2_name)
        self.core.add_ai_opponent("AI-Alpha", "The Maverick")
        self.core.add_ai_opponent("AI-Beta", "The Sentinel")

    def start_triple_threat_game(self, player1_id: int, player1_name: str, player2_id: int, player2_name: str):
        self.core.game_mode = "triple_threat"
        self.core.add_player(player1_id, player1_name)
        self.core.add_player(player2_id, player2_name)
        self.core.add_ai_opponent("CipherBot", "The Calculon")
