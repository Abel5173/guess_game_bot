import sqlite3
import logging

logger = logging.getLogger(__name__)

def get_player_stats(user_id: int):
    """Retrieves a player's stats from the database."""
    conn = sqlite3.connect("db.sqlite3")
    cursor = conn.cursor()
    cursor.execute(
        "SELECT xp, level, games_played, wins, losses FROM player_stats WHERE user_id = ?",
        (user_id,),
    )
    stats = cursor.fetchone()
    conn.close()
    if stats:
        return {
            "xp": stats[0],
            "level": stats[1],
            "games_played": stats[2],
            "wins": stats[3],
            "losses": stats[4],
        }
    return None

def update_player_stats(user_id: int, xp_gain: int = 0, won: bool = False):
    """Updates a player's stats after a game."""
    conn = sqlite3.connect("db.sqlite3")
    cursor = conn.cursor()

    # Get current stats
    cursor.execute(
        "SELECT xp, level, games_played, wins, losses FROM player_stats WHERE user_id = ?",
        (user_id,),
    )
    stats = cursor.fetchone()

    if not stats:
        # Create a new player entry
        cursor.execute(
            "INSERT INTO player_stats (user_id, xp, level, games_played, wins, losses) VALUES (?, ?, ?, ?, ?, ?)",
            (user_id, xp_gain, 1, 1, 1 if won else 0, 1 if not won else 0),
        )
    else:
        # Update existing stats
        new_xp = stats[0] + xp_gain
        new_games_played = stats[2] + 1
        new_wins = stats[3] + (1 if won else 0)
        new_losses = stats[4] + (1 if not won else 0)
        
        # Simple leveling system: 100 XP per level
        new_level = (new_xp // 100) + 1

        cursor.execute(
            "UPDATE player_stats SET xp = ?, level = ?, games_played = ?, wins = ?, losses = ? WHERE user_id = ?",
            (new_xp, new_level, new_games_played, new_wins, new_losses, user_id),
        )
    
    conn.commit()
    conn.close()
    logger.info(f"Updated stats for user {user_id}: xp_gain={xp_gain}, won={won}")

def get_leaderboard(limit: int = 10):
    """Retrieves the top players by XP."""
    conn = sqlite3.connect("db.sqlite3")
    cursor = conn.cursor()
    cursor.execute(
        "SELECT user_id, xp, level FROM player_stats ORDER BY xp DESC LIMIT ?", (limit,)
    )
    leaderboard = cursor.fetchall()
    conn.close()
    return leaderboard
