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

    def to_dict(self):
        return {
            "user_id": str(self.user_id),
            "name": self.name,
            "role": self.role,
            "is_alive": str(self.is_alive),
            "trust_points": str(self.trust_points),
            "credibility": str(self.credibility),
            "location": self.location,
        }
