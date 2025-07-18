# This will define the Player class, which will hold information about each player, such as their role, status, and abilities.
class Player:
    def __init__(self, user_id, name):
        self.user_id = user_id
        self.name = name
        self.role = None
        self.is_alive = True
        self.trust_points = 100
        self.credibility = 100
        self.location = "Lobby"
