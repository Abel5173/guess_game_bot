# Future in-game events (sabotage, rewards, etc.) will go here.

from typing import Dict, Set, Any
from bot.database import SessionLocal
from bot.database.models import Player
from bot.impostor.utils import calculate_title


def award_xp(user_id: int, amount: int, reason: str = "") -> None:
    db = SessionLocal()
    try:
        player = db.query(Player).filter(Player.id == user_id).first()
        if player:
            player.xp += amount
            player.title = calculate_title(player.xp)
            db.commit()
    finally:
        db.close()


def award_win_bonus(
    players: Dict[int, Any], impostors: Set[int], winning_team: str
) -> None:
    for uid in players:
        is_impostor = uid in impostors
        if winning_team == "crewmates" and not is_impostor:
            award_xp(uid, 20, "Crewmate win")
        elif winning_team == "impostors" and is_impostor:
            award_xp(uid, 30, "Impostor win")


def handle_vote_xp(
    votes: Dict[int, Any], voted_out_id: int, impostors: Set[int]
) -> None:
    is_impostor = voted_out_id in impostors
    for voter_id, target_id in votes.items():
        if target_id == voted_out_id and is_impostor:
            award_xp(voter_id, 20, "Correctly voted out impostor")
        elif target_id == voted_out_id and not is_impostor:
            award_xp(voter_id, -5, "Voted out crewmate")
    if is_impostor:
        award_xp(voted_out_id, -10, "Ejected as impostor")
