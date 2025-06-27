from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.sql import func
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