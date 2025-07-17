from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    DateTime,
    BigInteger,
    ForeignKey,
    Text,
    JSON,
)
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from bot.database import Base


class Player(Base):
    __tablename__ = "players"

    id = Column(Integer, primary_key=True, index=True)  # Telegram user ID
    name = Column(String, nullable=False)
    xp = Column(Integer, default=0)
    title = Column(String, default="Rookie")
    tasks_done = Column(Integer, default=0)
    fake_tasks_done = Column(Integer, default=0)
    wins = Column(Integer, default=0)
    losses = Column(Integer, default=0)

    # Engagement features
    trophies = Column(JSON, nullable=True)  # Store trophies as JSON
    room_theme = Column(String, default="default")  # Player's room theme
    room_layout = Column(String, default="default")  # Player's room layout
    badges = Column(JSON, nullable=True)  # Store badges as JSON
    missions_completed = Column(Integer, default=0)  # Total missions completed
    streak_days = Column(Integer, default=0)  # Current streak
    last_mission_date = Column(
        DateTime(timezone=True), nullable=True
    )  # Last mission completion


class Task(Base):
    __tablename__ = "tasks"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)
    chat_id = Column(Integer, index=True)
    task_type = Column(String)
    puzzle = Column(String)
    answer = Column(String)
    status = Column(String, default="pending")  # pending/completed/failed
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    team_id = Column(Integer, nullable=True)  # For group/team tasks
    is_group_task = Column(Boolean, default=False)


class GameSession(Base):
    """Database model for game sessions (topics)"""

    __tablename__ = "game_sessions"

    id = Column(Integer, primary_key=True, index=True)
    topic_id = Column(BigInteger, unique=True, index=True)  # Telegram topic ID
    chat_id = Column(BigInteger, index=True)  # Telegram chat ID
    game_type = Column(String, default="impostor")  # impostor, guess, etc.
    status = Column(String, default="waiting")  # waiting, active, finished, abandoned
    creator_id = Column(Integer, index=True)  # Telegram user ID of creator
    topic_name = Column(String)
    max_players = Column(Integer, default=10)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    started_at = Column(DateTime(timezone=True), nullable=True)
    finished_at = Column(DateTime(timezone=True), nullable=True)

    # Game state (JSON for flexibility)
    game_state = Column(JSON, nullable=True)  # Store game-specific state

    # Engagement features
    flash_event_id = Column(String, nullable=True)  # If part of a flash event
    risk_reward_mode = Column(Boolean, default=False)  # If risk-reward mode is active

    # Relationships
    players = relationship("PlayerGameLink", back_populates="session")
    votes = relationship("VoteHistory", back_populates="session")
    discussions = relationship("DiscussionLog", back_populates="session")
    tasks = relationship("TaskLog", back_populates="session")


class PlayerGameLink(Base):
    """Link table connecting players to game sessions"""

    __tablename__ = "player_game_links"

    id = Column(Integer, primary_key=True, index=True)
    player_id = Column(Integer, ForeignKey("players.id"), index=True)
    session_id = Column(Integer, ForeignKey("game_sessions.id"), index=True)
    role = Column(String, default="crewmate")  # crewmate, impostor, spectator
    joined_at = Column(DateTime(timezone=True), server_default=func.now())
    left_at = Column(DateTime(timezone=True), nullable=True)
    outcome = Column(String, nullable=True)  # win, lose, ejected, left
    xp_earned = Column(Integer, default=0)

    # Engagement features
    wager_amount = Column(Integer, default=0)  # XP wagered in risk-reward mode
    wager_multiplier = Column(Integer, default=1)  # Wager multiplier
    mvp = Column(Boolean, default=False)  # If player was MVP
    tasks_completed = Column(Integer, default=0)  # Tasks completed in this game
    correct_votes = Column(Integer, default=0)  # Correct votes in this game

    # Relationships
    player = relationship("Player")
    session = relationship("GameSession", back_populates="players")


class PlayerPerformance(Base):
    __tablename__ = "player_performance"

    id = Column(Integer, primary_key=True, index=True)
    player_id = Column(Integer, ForeignKey("players.id"), unique=True, index=True)
    wins = Column(Integer, default=0)
    losses = Column(Integer, default=0)
    average_guesses_to_win = Column(Integer, default=0)
    skill_rating = Column(Integer, default=1000)  # Elo-style rating

    player = relationship("Player")


class VoteHistory(Base):
    """Track voting history for analytics"""

    __tablename__ = "vote_history"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("game_sessions.id"), index=True)
    voter_id = Column(Integer, ForeignKey("players.id"), index=True)
    target_id = Column(Integer, ForeignKey("players.id"), index=True)
    round_number = Column(Integer, default=1)
    vote_type = Column(String, default="eject")  # eject, skip
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

    # Engagement features
    anonymous_vote = Column(Boolean, default=False)  # If vote was anonymous
    double_vote = Column(Boolean, default=False)  # If vote counted twice
    sabotage_vote = Column(Boolean, default=False)  # If vote was sabotaged

    # Relationships
    session = relationship("GameSession", back_populates="votes")
    voter = relationship("Player", foreign_keys=[voter_id])
    target = relationship("Player", foreign_keys=[target_id])


class DiscussionLog(Base):
    """Log discussion messages for analytics"""

    __tablename__ = "discussion_logs"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("game_sessions.id"), index=True)
    player_id = Column(Integer, ForeignKey("players.id"), index=True)
    message = Column(Text)
    phase = Column(String, default="discussion")  # discussion, voting, task
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

    # Engagement features
    whisper_target = Column(Integer, nullable=True)  # If this was a whisper
    persona_challenge = Column(String, nullable=True)  # If part of persona challenge

    # Relationships
    session = relationship("GameSession", back_populates="discussions")
    player = relationship("Player")


class TaskLog(Base):
    """Log task completions for analytics"""

    __tablename__ = "task_logs"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("game_sessions.id"), index=True)
    player_id = Column(Integer, ForeignKey("players.id"), index=True)
    task_type = Column(String)  # ai_riddle, emoji_decode, etc.
    task_description = Column(Text)
    xp_earned = Column(Integer, default=0)
    completed_at = Column(DateTime(timezone=True), server_default=func.now())

    # Engagement features
    fake_task = Column(Boolean, default=False)  # If this was a fake task
    betrayal_card_used = Column(String, nullable=True)  # If betrayal card was used

    # Relationships
    session = relationship("GameSession", back_populates="tasks")
    player = relationship("Player")


class GameLog(Base):
    """Store AI-generated game summaries and logs"""

    __tablename__ = "game_logs"

    id = Column(Integer, primary_key=True, index=True)
    log_data = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class JoinQueue(Base):
    """Track users waiting to join games"""

    __tablename__ = "join_queue"

    id = Column(Integer, primary_key=True, index=True)
    player_id = Column(Integer, ForeignKey("players.id"), index=True)
    chat_id = Column(BigInteger, index=True)
    joined_at = Column(DateTime(timezone=True), server_default=func.now())
    notified_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    player = relationship("Player")


# New tables for engagement features


class MissionProgress(Base):
    """Track mission progress for players"""

    __tablename__ = "mission_progress"

    id = Column(Integer, primary_key=True, index=True)
    player_id = Column(Integer, ForeignKey("players.id"), index=True)
    mission_id = Column(String, index=True)  # Mission identifier
    mission_type = Column(String)  # daily, weekly, seasonal, special
    progress = Column(Integer, default=0)  # Current progress
    required = Column(Integer)  # Required amount to complete
    completed = Column(Boolean, default=False)  # If mission is completed
    claimed = Column(Boolean, default=False)  # If rewards were claimed
    assigned_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True))  # When mission expires

    # Relationships
    player = relationship("Player")


class FlashEvent(Base):
    """Track flash events"""

    __tablename__ = "flash_events"

    id = Column(String, primary_key=True)  # Event identifier
    name = Column(String, nullable=False)
    description = Column(Text)
    event_type = Column(String)  # friday_night, weekend_warrior, etc.
    start_time = Column(DateTime(timezone=True), nullable=False)
    end_time = Column(DateTime(timezone=True), nullable=False)
    max_players = Column(Integer, default=50)
    rewards = Column(JSON)  # Event rewards as JSON
    status = Column(String, default="upcoming")  # upcoming, active, finished

    created_at = Column(DateTime(timezone=True), server_default=func.now())


class FlashEventParticipant(Base):
    """Track flash event participants"""

    __tablename__ = "flash_event_participants"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(String, ForeignKey("flash_events.id"), index=True)
    player_id = Column(Integer, ForeignKey("players.id"), index=True)
    joined_at = Column(DateTime(timezone=True), server_default=func.now())
    xp_earned = Column(Integer, default=0)

    # Relationships
    event = relationship("FlashEvent")
    player = relationship("Player")


class ShareableResult(Base):
    """Store shareable game results"""

    __tablename__ = "shareable_results"

    id = Column(String, primary_key=True)  # Result identifier
    player_id = Column(Integer, ForeignKey("players.id"), index=True)
    game_id = Column(String, index=True)  # Game identifier
    result_data = Column(JSON)  # Game result data as JSON
    share_count = Column(Integer, default=0)  # Number of times shared
    reactions = Column(JSON, nullable=True)  # Reactions as JSON
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    player = relationship("Player")
