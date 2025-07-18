# This will handle the game state, including player status, roles, and game room data.
# It will use Redis for real-time updates and PostgreSQL for persistent storage.
import redis
from sqlalchemy.orm import sessionmaker
from bot.database import engine

# Redis connection
r = redis.Redis(decode_responses=True)

# SQLAlchemy session
Session = sessionmaker(bind=engine)
session = Session()


def get_game_state(chat_id):
    return r.hgetall(f"game:{chat_id}")


def update_game_state(chat_id, data):
    r.hmset(f"game:{chat_id}", data)


def get_player_state(chat_id, user_id):
    return r.hgetall(f"game:{chat_id}:player:{user_id}")


def update_player_state(chat_id, user_id, data):
    r.hmset(f"game:{chat_id}:player:{user_id}", data)
