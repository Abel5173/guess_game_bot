from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from bot.database import Base
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.types import JSON
import datetime

Base = declarative_base()

class Player(Base):
    __tablename__ = "players"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, unique=True, index=True)
    username = Column(String, unique=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Task(Base):
    __tablename__ = "tasks"
    id = Column(Integer, primary_key=True, index=True)
    description = Column(String, index=True)
    is_completed = Column(Boolean, default=False)
    player_id = Column(Integer, ForeignKey("players.id"))
    player = relationship("Player")

class PlayerStats(Base):
    __tablename__ = "player_stats"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, unique=True, index=True)
    xp = Column(Integer, default=0)
    level = Column(Integer, default=1)
    games_played = Column(Integer, default=0)
    wins = Column(Integer, default=0)
    losses = Column(Integer, default=0)

class GameSession(Base):
    __tablename__ = "game_sessions"
    id = Column(Integer, primary_key=True, index=True)
    chat_id = Column(Integer, index=True)
    game_mode = Column(String, index=True)
    start_time = Column(DateTime(timezone=True), server_default=func.now())
    end_time = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, default=True)
    winner_id = Column(Integer, ForeignKey("players.id"), nullable=True)
    winner = relationship("Player", foreign_keys=[winner_id])
    current_state = Column(String) # Store game-specific state as JSON string

class GameLog(Base):
    __tablename__ = "game_logs"
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("game_sessions.id"))
    session = relationship("GameSession")
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    event_type = Column(String)
    event_data = Column(String) # Store event details as JSON string
    player_id = Column(Integer, ForeignKey("players.id"), nullable=True)
    player = relationship("Player", foreign_keys=[player_id])

class PlayerGameLink(Base):
    __tablename__ = "player_game_link"
    id = Column(Integer, primary_key=True, index=True)
    player_id = Column(Integer, ForeignKey("players.id"))
    session_id = Column(Integer, ForeignKey("game_sessions.id"))
    role = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    score = Column(Integer, default=0)
    player = relationship("Player", foreign_keys=[player_id])
    game_session = relationship("GameSession", foreign_keys=[session_id])

class DiscussionLog(Base):
    __tablename__ = "discussion_logs"
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("game_sessions.id"))
    session = relationship("GameSession")
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    speaker_id = Column(Integer, ForeignKey("players.id"), nullable=True)
    speaker = relationship("Player", foreign_keys=[speaker_id])
    speaker_type = Column(String) # e.g., "player", "ai", "system"
    message = Column(String)

class TaskLog(Base):
    __tablename__ = "task_logs"
    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id"))
    task = relationship("Task")
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    event_type = Column(String)
    details = Column(String)
    player_id = Column(Integer, ForeignKey("players.id"), nullable=True)
    player = relationship("Player", foreign_keys=[player_id])

class VoteHistory(Base):
    __tablename__ = "vote_history"
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("game_sessions.id"))
    session = relationship("GameSession")
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    voter_id = Column(Integer, ForeignKey("players.id"))
    voter = relationship("Player", foreign_keys=[voter_id], primaryjoin="Player.id == VoteHistory.voter_id")
    candidate_id = Column(Integer, ForeignKey("players.id"))
    candidate = relationship("Player", foreign_keys=[candidate_id], primaryjoin="Player.id == VoteHistory.candidate_id")
    vote_type = Column(String) # e.g., "elimination", "task_assignment"

class ActiveGame(Base):
    __tablename__ = 'active_games'
    chat_id = Column(Integer, primary_key=True)
    mode = Column(String, nullable=False)  # 'pvp', 'group_ai', 'group_pvp'
    data = Column(JSON, nullable=False)
    last_activity = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

class GameStats(Base):
    __tablename__ = 'game_stats'
    id = Column(Integer, primary_key=True, autoincrement=True)
    chat_id = Column(Integer, nullable=False)
    game_mode = Column(String, nullable=False)  # 'pvp', 'group_ai', 'group_pvp'
    player_id = Column(Integer, nullable=True)  # Null for team stats
    team = Column(String, nullable=True)        # 'A', 'B', or None
    result = Column(String, nullable=False)     # 'win', 'loss', 'draw'
    guesses = Column(Integer, nullable=False)
    max_stress = Column(Integer, nullable=False)
    duration = Column(Integer, nullable=True)   # seconds
    mvp = Column(Boolean, default=False)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
