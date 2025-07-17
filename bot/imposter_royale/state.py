# This will handle the game state, including player status, roles, and game room data.
import redis

class GameState:
    def __init__(self, chat_id):
        self.r = redis.Redis(decode_responses=True)
        self.chat_id = chat_id
        self.game_key = f"game:{chat_id}"

    def set_phase(self, phase):
        self.r.hset(self.game_key, "phase", phase)

    def get_phase(self):
        return self.r.hget(self.game_key, "phase")

    def add_player(self, player):
        player_key = f"{self.game_key}:player:{player.user_id}"
        player_data = {k: v for k, v in player.to_dict().items() if v is not None}
        self.r.hmset(player_key, player_data)

    def get_all_players(self):
        player_keys = self.r.keys(f"{self.game_key}:player:*")
        players = []
        for key in player_keys:
            players.append(self.r.hgetall(key))
        return players

    def update_player_location(self, user_id, room):
        player_key = f"{self.game_key}:player:{user_id}"
        self.r.hset(player_key, "location", room)

    def update_player_status(self, user_id, status):
        player_key = f"{self.game_key}:player:{user_id}"
        self.r.hset(player_key, "status", status)

    def log_event(self, event_type, data):
        event_key = f"{self.game_key}:events"
        self.r.lpush(event_key, f"{event_type}:{data}")

    def add_vote(self, voter_id, target_id):
        vote_key = f"{self.game_key}:votes"
        self.r.hset(vote_key, voter_id, target_id)

    def get_votes(self):
        return self.r.hgetall(f"{self.game_key}:votes")

    def clear_votes(self):
        self.r.delete(f"{self.game_key}:votes")
