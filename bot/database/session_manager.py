"""
Database session manager for game sessions and analytics.
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc, func
from datetime import datetime, timedelta
from bot.database import SessionLocal
from bot.database.models import (
    GameSession,
    PlayerGameLink,
    VoteHistory,
    DiscussionLog,
    TaskLog,
    JoinQueue,
    Player,
)
import logging

logger = logging.getLogger(__name__)


class GameSessionManager:
    """Manages game sessions in the database."""

    def __init__(self):
        self.db = SessionLocal()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.db.close()

    def create_session(
        self,
        topic_id: int,
        chat_id: int,
        creator_id: int,
        topic_name: str,
        game_type: str = "impostor",
    ) -> GameSession:
        """Create a new game session."""
        session = GameSession(
            topic_id=topic_id,
            chat_id=chat_id,
            creator_id=creator_id,
            topic_name=topic_name,
            game_type=game_type,
            status="waiting",
        )
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)
        logger.info(f"Created game session {session.id} for topic {topic_id}")
        return session

    def get_session_by_topic(self, topic_id: int) -> Optional[GameSession]:
        """Get game session by topic ID."""
        return (
            self.db.query(GameSession).filter(GameSession.topic_id == topic_id).first()
        )

    def get_active_sessions(self, chat_id: Optional[int] = None) -> List[GameSession]:
        """Get all active game sessions."""
        query = self.db.query(GameSession).filter(
            GameSession.status.in_(["waiting", "active"])
        )
        if chat_id:
            query = query.filter(GameSession.chat_id == chat_id)
        return query.all()

    def update_session_status(
        self, topic_id: int, status: str, game_state: Optional[Dict] = None
    ) -> bool:
        """Update session status and optionally game state."""
        session = self.get_session_by_topic(topic_id)
        if not session:
            return False

        session.status = status
        if status == "active" and not session.started_at:
            session.started_at = datetime.now()
        elif status == "finished" and not session.finished_at:
            session.finished_at = datetime.now()

        if game_state is not None:
            session.game_state = game_state

        self.db.commit()
        logger.info(f"Updated session {session.id} status to {status}")
        return True

    def add_player_to_session(
        self, session_id: int, player_id: int, role: str = "crewmate"
    ) -> PlayerGameLink:
        """Add a player to a game session."""
        # Check if player is already in session
        existing = (
            self.db.query(PlayerGameLink)
            .filter(
                and_(
                    PlayerGameLink.session_id == session_id,
                    PlayerGameLink.player_id == player_id,
                    PlayerGameLink.left_at.is_(None),
                )
            )
            .first()
        )

        if existing:
            return existing

        link = PlayerGameLink(session_id=session_id, player_id=player_id, role=role)
        self.db.add(link)
        self.db.commit()
        self.db.refresh(link)
        logger.info(f"Added player {player_id} to session {session_id}")
        return link

    def remove_player_from_session(self, session_id: int, player_id: int) -> bool:
        """Remove a player from a game session."""
        link = (
            self.db.query(PlayerGameLink)
            .filter(
                and_(
                    PlayerGameLink.session_id == session_id,
                    PlayerGameLink.player_id == player_id,
                    PlayerGameLink.left_at.is_(None),
                )
            )
            .first()
        )

        if link:
            link.left_at = datetime.now()
            self.db.commit()
            logger.info(f"Removed player {player_id} from session {session_id}")
            return True
        return False

    def get_session_players(self, session_id: int) -> List[PlayerGameLink]:
        """Get all players in a session."""
        return (
            self.db.query(PlayerGameLink)
            .filter(
                and_(
                    PlayerGameLink.session_id == session_id,
                    PlayerGameLink.left_at.is_(None),
                )
            )
            .all()
        )

    def log_vote(
        self,
        session_id: int,
        voter_id: int,
        target_id: int,
        round_number: int = 1,
        vote_type: str = "eject",
    ) -> VoteHistory:
        """Log a vote in the database."""
        vote = VoteHistory(
            session_id=session_id,
            voter_id=voter_id,
            target_id=target_id,
            round_number=round_number,
            vote_type=vote_type,
        )
        self.db.add(vote)
        self.db.commit()
        self.db.refresh(vote)
        return vote

    def log_discussion(
        self, session_id: int, player_id: int, message: str, phase: str = "discussion"
    ) -> DiscussionLog:
        """Log a discussion message."""
        discussion = DiscussionLog(
            session_id=session_id, player_id=player_id, message=message, phase=phase
        )
        self.db.add(discussion)
        self.db.commit()
        self.db.refresh(discussion)
        return discussion

    def log_task_completion(
        self,
        session_id: int,
        player_id: int,
        task_type: str,
        task_description: str,
        xp_earned: int = 0,
    ) -> TaskLog:
        """Log a task completion."""
        task_log = TaskLog(
            session_id=session_id,
            player_id=player_id,
            task_type=task_type,
            task_description=task_description,
            xp_earned=xp_earned,
        )
        self.db.add(task_log)
        self.db.commit()
        self.db.refresh(task_log)
        return task_log

    def cleanup_old_sessions(self, max_age_hours: int = 24) -> int:
        """Clean up old finished/abandoned sessions."""
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
        old_sessions = (
            self.db.query(GameSession)
            .filter(
                and_(
                    GameSession.status.in_(["finished", "abandoned"]),
                    GameSession.finished_at < cutoff_time,
                )
            )
            .all()
        )

        count = len(old_sessions)
        for session in old_sessions:
            self.db.delete(session)

        self.db.commit()
        logger.info(f"Cleaned up {count} old game sessions")
        return count


class JoinQueueManager:
    """Manages the join queue in the database."""

    def __init__(self):
        self.db = SessionLocal()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.db.close()

    def add_to_queue(self, player_id: int, chat_id: int) -> bool:
        """Add a player to the join queue."""
        # Check if already in queue
        existing = (
            self.db.query(JoinQueue)
            .filter(
                and_(
                    JoinQueue.player_id == player_id,
                    JoinQueue.chat_id == chat_id,
                    JoinQueue.notified_at.is_(None),
                )
            )
            .first()
        )

        if existing:
            return False

        queue_entry = JoinQueue(player_id=player_id, chat_id=chat_id)
        self.db.add(queue_entry)
        self.db.commit()
        logger.info(f"Added player {player_id} to join queue for chat {chat_id}")
        return True

    def get_queue(self, chat_id: Optional[int] = None) -> List[JoinQueue]:
        """Get all players in the queue."""
        query = self.db.query(JoinQueue).filter(JoinQueue.notified_at.is_(None))
        if chat_id:
            query = query.filter(JoinQueue.chat_id == chat_id)
        return query.all()

    def remove_from_queue(self, player_id: int, chat_id: Optional[int] = None) -> bool:
        """Remove a player from the join queue."""
        query = self.db.query(JoinQueue).filter(
            and_(JoinQueue.player_id == player_id, JoinQueue.notified_at.is_(None))
        )
        if chat_id:
            query = query.filter(JoinQueue.chat_id == chat_id)

        queue_entry = query.first()
        if queue_entry:
            self.db.delete(queue_entry)
            self.db.commit()
            logger.info(f"Removed player {player_id} from join queue")
            return True
        return False

    def notify_queue(self, chat_id: int) -> List[int]:
        """Mark all queued players as notified and return their IDs."""
        queue_entries = self.get_queue(chat_id)
        player_ids = [entry.player_id for entry in queue_entries]

        for entry in queue_entries:
            entry.notified_at = datetime.now()

        self.db.commit()
        logger.info(f"Notified {len(player_ids)} players in queue for chat {chat_id}")
        return player_ids

    def cleanup_old_queue(self, max_age_hours: int = 6) -> int:
        """Clean up old queue entries."""
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
        old_entries = (
            self.db.query(JoinQueue).filter(JoinQueue.joined_at < cutoff_time).all()
        )

        count = len(old_entries)
        for entry in old_entries:
            self.db.delete(entry)

        self.db.commit()
        logger.info(f"Cleaned up {count} old queue entries")
        return count


class AnalyticsManager:
    """Manages analytics queries."""

    def __init__(self):
        self.db = SessionLocal()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.db.close()

    def get_player_stats(self, player_id: int) -> Dict[str, Any]:
        """Get comprehensive stats for a player."""
        # Get basic player info
        player = self.db.query(Player).filter(Player.id == player_id).first()
        if not player:
            return {}

        # Get game participation stats
        games_played = (
            self.db.query(PlayerGameLink)
            .filter(PlayerGameLink.player_id == player_id)
            .count()
        )

        games_won = (
            self.db.query(PlayerGameLink)
            .filter(
                and_(
                    PlayerGameLink.player_id == player_id,
                    PlayerGameLink.outcome == "win",
                )
            )
            .count()
        )

        total_xp_earned = (
            self.db.query(PlayerGameLink)
            .filter(PlayerGameLink.player_id == player_id)
            .with_entities(func.sum(PlayerGameLink.xp_earned))
            .scalar()
            or 0
        )

        return {
            "player": player,
            "games_played": games_played,
            "games_won": games_won,
            "win_rate": games_won / games_played if games_played > 0 else 0,
            "total_xp_earned": total_xp_earned,
        }

    def get_session_leaderboard(self, session_id: int) -> List[Dict[str, Any]]:
        """Get leaderboard for a specific session."""
        players = (
            self.db.query(PlayerGameLink)
            .filter(PlayerGameLink.session_id == session_id)
            .join(Player)
            .order_by(desc(PlayerGameLink.xp_earned))
            .all()
        )

        leaderboard = []
        for i, player_link in enumerate(players, 1):
            leaderboard.append(
                {
                    "rank": i,
                    "player_name": player_link.player.name,
                    "xp_earned": player_link.xp_earned,
                    "role": player_link.role,
                    "outcome": player_link.outcome,
                }
            )

        return leaderboard

    def get_chat_stats(self, chat_id: int, days: int = 7) -> Dict[str, Any]:
        """Get stats for a specific chat."""
        cutoff_date = datetime.now() - timedelta(days=days)

        sessions = (
            self.db.query(GameSession)
            .filter(
                and_(
                    GameSession.chat_id == chat_id,
                    GameSession.created_at >= cutoff_date,
                )
            )
            .all()
        )

        total_sessions = len(sessions)
        active_sessions = len(
            [s for s in sessions if s.status in ["waiting", "active"]]
        )
        finished_sessions = len([s for s in sessions if s.status == "finished"])

        return {
            "total_sessions": total_sessions,
            "active_sessions": active_sessions,
            "finished_sessions": finished_sessions,
            "completion_rate": (
                finished_sessions / total_sessions if total_sessions > 0 else 0
            ),
        }
