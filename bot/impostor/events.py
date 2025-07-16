# Future in-game events (sabotage, rewards, etc.) will go here.
import logging
from typing import Dict, Set, Any, List
from bot.database import SessionLocal
from bot.database.models import Player, GameLog
from bot.impostor.utils import calculate_title
from bot.ai.llm_client import ai_client

logger = logging.getLogger(__name__)


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


async def generate_game_summary(game_log: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Generates a game summary using the AI client.
    """
    try:
        summary = await ai_client.generate_game_summary(game_log)
        # Add to database
        db = SessionLocal()
        try:
            db.add(GameLog(log_data=summary))
            db.commit()
        finally:
            db.close()
        return summary
    except Exception as e:
        logger.error(f"Error generating game summary: {e}")
        return {
            "winning_team": "unknown",
            "narrative": "The game concluded, but the station's logs were corrupted.",
            "mvp": {"name": "N/A", "reason": "Data unavailable"},
            "notable_plays": [],
            "final_verdict": "The true story may never be known.",
        }
