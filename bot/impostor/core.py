# Core game state, player/role management, and game start/reset will go here.

import random
from typing import Dict, Set, Optional, Tuple, Any, List
from bot.database.models import Player
from bot.database import SessionLocal
from bot.impostor.events import award_xp, award_win_bonus, handle_vote_xp
from bot.ai.chaos_events import ai_chaos_events
import logging

logger = logging.getLogger(__name__)


class ImpostorCore:
    """
    Core state and player/role management for the Impostor Game.
    Handles player joining, role assignment, game start, reset, XP, and title leveling.
    Uses a database for persistent player stats.
    """

    def __init__(self, config: Optional[dict] = None) -> None:
        logger.debug("Initializing ImpostorCore")
        # user_id: {'name': name, 'alive': True}
        self.players: Dict[int, dict] = {}
        self.group_chat_id: Optional[int] = None
        self.started: bool = False
        self.impostors: Set[int] = set()
        self.phase: str = "waiting"
        self.votes: Dict[int, Optional[int]] = {}
        self.round = 0
        self.game_log: List[Dict[str, Any]] = []
        self.config = config or {
            "min_players": 4,
            "impostor_count": 1,
            "tasks_required": 2,
            "anonymous_voting": True,
        }
        logger.info(f"ImpostorCore initialized with config: {self.config}")

    def add_player(self, user_id: int, name: str) -> bool:
        logger.info(f"add_player called with user_id={user_id}, name={name}")
        if self.started or user_id in self.players:
            logger.warning(
                f"Cannot add player {user_id}: game started or already present."
            )
            return False
        self.players[user_id] = {"name": name, "alive": True}
        db = SessionLocal()
        player = db.query(Player).filter(Player.id == user_id).first()
        if not player:
            db.add(Player(id=user_id, name=name))
            db.commit()
        db.close()
        logger.info(f"Player {user_id} added successfully.")
        return True

    def assign_roles(self) -> None:
        logger.info("assign_roles called")
        all_ids = list(self.players.keys())
        self.impostors = set(random.sample(all_ids, self.config["impostor_count"]))
        logger.info(f"Roles assigned: impostors={self.impostors}")

    def start_game(self) -> bool:
        """Start the game if enough players have joined. Returns True if started."""
        if len(self.players) < self.config["min_players"]:
            return False
        self.started = True
        self.phase = "task"
        self.round = 1
        self.assign_roles()
        self.log_event("game_start", {"players": self.players})
        ai_chaos_events.cleanup_session_events(self.group_chat_id)
        return True

    def get_alive_players(self) -> Dict[int, dict]:
        return {uid: player for uid, player in self.players.items() if player["alive"]}

    def vote(self, voter_id: int, target_id: int) -> bool:
        if voter_id in self.players and target_id in self.players:
            self.votes[voter_id] = target_id
            award_xp(voter_id, 5, "Vote cast")
            return True
        return False

    def resolve_votes(self) -> Tuple[Optional[int], str]:
        counts: Dict[int, int] = {}
        for target in self.votes.values():
            if target is not None:
                counts[target] = counts.get(target, 0) + 1
        if not counts:
            return None, "No one was ejected."
        max_votes = max(counts.values())
        candidates = [uid for uid, v in counts.items() if v == max_votes]
        if len(candidates) > 1:
            return None, "It's a tie! No one was ejected."
        voted_out = candidates[0]
        self.players[voted_out]["alive"] = False
        handle_vote_xp(self.votes, voted_out, self.impostors)
        self.votes.clear()
        self.round += 1
        self.log_event(
            "vote_end",
            {
                "voted_out": voted_out,
                "impostor": voted_out in self.impostors,
                "round": self.round,
            },
        )
        return voted_out, f"{self.players[voted_out]['name']} was ejected!"

    def check_game_over(self) -> Tuple[bool, str, Optional[str]]:
        impostors_alive = len(
            [
                uid
                for uid in self.players
                if uid in self.impostors and self.players[uid]["alive"]
            ]
        )
        crewmates_alive = len(
            [
                uid
                for uid in self.players
                if uid not in self.impostors and self.players[uid]["alive"]
            ]
        )
        if impostors_alive == 0:
            award_win_bonus(self.players, self.impostors, "crewmates")
            return True, "🎉 Crewmates win!", "crewmates"
        if impostors_alive > crewmates_alive:
            award_win_bonus(self.players, self.impostors, "impostors")
            return True, "💀 Impostor wins!", "impostors"
        game_over, message, winner = (False, "", None)
        impostors_alive = len(
            [
                uid
                for uid in self.players
                if uid in self.impostors and self.players[uid]["alive"]
            ]
        )
        crewmates_alive = len(
            [
                uid
                for uid in self.players
                if uid not in self.impostors and self.players[uid]["alive"]
            ]
        )
        if impostors_alive == 0:
            award_win_bonus(self.players, self.impostors, "crewmates")
            game_over, message, winner = True, "🎉 Crewmates win!", "crewmates"
        if impostors_alive > crewmates_alive:
            award_win_bonus(self.players, self.impostors, "impostors")
            game_over, message, winner = True, "💀 Impostor wins!", "impostors"

        if game_over:
            self.log_event("game_over", {"winner": winner})
            ai_chaos_events.cleanup_session_events(self.group_chat_id)

        return game_over, message, winner

    def get_profile(self, user_id: int) -> Optional[Player]:
        db = SessionLocal()
        player = db.query(Player).filter(Player.id == user_id).first()
        db.close()
        return player

    def get_leaderboard(self, top_n: int = 10) -> list[Player]:
        db = SessionLocal()
        top_players = db.query(Player).order_by(Player.xp.desc()).limit(top_n).all()
        db.close()
        return top_players

    def reset(self) -> None:
        """Reset the game state for a new game."""
        self.players.clear()
        self.group_chat_id = None
        self.started = False
        self.impostors.clear()
        self.phase = "waiting"
        self.votes = {}
        self.round = 0
        self.game_log = []

    def log_event(self, event_type: str, data: Dict[str, Any]) -> None:
        """Logs a game event for AI summary generation."""
        self.game_log.append(
            {"timestamp": self.round, "event_type": event_type, "data": data}
        )
