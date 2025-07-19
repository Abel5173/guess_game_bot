import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from game.ai_vs_player import PvPGameSession
import json
import os

logger = logging.getLogger(__name__)

# In-memory store for active PvP sessions: (player1_id, player2_id) -> PvPGameSession
active_pvp_sessions = {}
LEADERBOARD_FILE = "pvp_leaderboard.json"

def save_leaderboard(leaderboard):
    with open(LEADERBOARD_FILE, "w") as f:
        json.dump(leaderboard, f)

def load_leaderboard():
    if not os.path.exists(LEADERBOARD_FILE):
        return {}
    with open(LEADERBOARD_FILE, "r") as f:
        return json.load(f)

def get_session_key(user1, user2):
    return tuple(sorted([user1, user2]))

async def start_pvp(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start a new PvP game session. Both players must set their code privately."""
    if not update.message.reply_to_message or not update.message.reply_to_message.from_user:
        await update.message.reply_text("Reply to your opponent's message with /start_pvp to begin.")
        return
    player1_id = update.effective_user.id
    player2_id = update.message.reply_to_message.from_user.id
    if player1_id == player2_id:
        await update.message.reply_text("You can't play against yourself!")
        return
    key = get_session_key(player1_id, player2_id)
    if key in active_pvp_sessions:
        await update.message.reply_text("A PvP game is already in progress between you two.")
        return
    active_pvp_sessions[key] = PvPGameSession(player1_id, player2_id)
    await update.message.reply_text(
        f"PvP game started between <b>{update.effective_user.full_name}</b> and <b>{update.message.reply_to_message.from_user.full_name}</b>!\nBoth players, please send /set_pvp_code <4 unique digits> in private chat with the bot.",
        parse_mode="HTML"
    )

async def set_pvp_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Each player sets their secret code privately."""
    user_id = update.effective_user.id
    # Find a session where this user is a participant
    session = None
    for key, s in active_pvp_sessions.items():
        if user_id in key:
            session = s
            break
    if not session:
        await update.message.reply_text("No active PvP game found. Start one in a group with /start_pvp.")
        return
    if not context.args or not session._is_valid_code(context.args[0]):
        await update.message.reply_text("Invalid code. Use /set_pvp_code <1234> (4 unique digits).")
        return
    session.set_code(user_id, context.args[0])
    await update.message.reply_text("Code set! Waiting for your opponent to set theirs." if len(session.codes) < 2 else "Both codes set! Game begins. Use /pvp_guess <1234> in the group chat on your turn.")

async def pvp_powerup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Use a power-up: /pvp_powerup <reveal_bull|extra_guess>"""
    user_id = update.effective_user.id
    key = None
    session = None
    for k, s in active_pvp_sessions.items():
        if user_id in k:
            key = k
            session = s
            break
    if not session or not session.ready():
        await update.message.reply_text("No active PvP game found or codes not set.")
        return
    if not context.args or context.args[0] not in ("reveal_bull", "extra_guess"):
        await update.message.reply_text("Usage: /pvp_powerup <reveal_bull|extra_guess>")
        return
    result = session.use_power_up(user_id, context.args[0])
    if "error" in result:
        await update.message.reply_text(result["error"])
        return
    if "reveal_bull" in result:
        i, digit = result["reveal_bull"]
        await update.message.reply_text(f"Power-Up: Revealed digit {digit} at position {i+1} (1-based index) in opponent's code!")
    elif "extra_guess" in result:
        await update.message.reply_text("Power-Up: You get an extra guess! Use /pvp_guess <1234> again.")

async def pvp_spectate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Add yourself as a spectator to a PvP session."""
    user_id = update.effective_user.id
    # For demo, join the first available session
    for session in active_pvp_sessions.values():
        session.add_spectator(user_id)
        await update.message.reply_text("You are now spectating this PvP game! Use /pvp_livefeed to see the action.")
        return
    await update.message.reply_text("No active PvP games to spectate.")

async def pvp_unspectate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Remove yourself as a spectator from all PvP sessions."""
    user_id = update.effective_user.id
    found = False
    for session in active_pvp_sessions.values():
        if user_id in session.spectators:
            session.remove_spectator(user_id)
            found = True
    if found:
        await update.message.reply_text("You are no longer spectating any PvP games.")
    else:
        await update.message.reply_text("You were not spectating any PvP games.")

async def pvp_livefeed(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show the live feed of guesses/results for spectators."""
    user_id = update.effective_user.id
    for session in active_pvp_sessions.values():
        if user_id in session.spectators:
            feed = session.get_live_feed()
            if not feed:
                await update.message.reply_text("No guesses made yet.")
                return
            msg = "Live Feed:\n"
            for uid, guess, bulls, cows in feed:
                msg += f"User {uid} guessed {guess}: {bulls} Bulls, {cows} Cows\n"
            await update.message.reply_text(msg)
            return
    await update.message.reply_text("You are not spectating any PvP games. Use /pvp_spectate to join.")

async def pvp_guess(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Player makes a guess in the group chat. Only allowed on your turn. Handles power-ups and streaks."""
    user_id = update.effective_user.id
    key = None
    session = None
    for k, s in active_pvp_sessions.items():
        if user_id in k:
            key = k
            session = s
            break
    if not session or not session.ready():
        await update.message.reply_text("No active PvP game found or codes not set.")
        return
    if not context.args or not session._is_valid_code(context.args[0]):
        await update.message.reply_text("Invalid guess. Use /pvp_guess <1234> (4 unique digits).")
        return
    # Check if player has extra_guess power-up active
    extra_guess_active = not session.power_ups[user_id]["extra_guess"] and session.turn == user_id
    result = session.make_guess(user_id, context.args[0])
    if "error" in result:
        await update.message.reply_text(result["error"])
        return
    msg = f"{update.effective_user.full_name} guessed {context.args[0]}: {result['bulls']} Bulls, {result['cows']} Cows."
    if result.get("streak_bonus"):
        msg += f"\n🔥 Streak Bonus! +{result['streak_bonus']} XP for {session.streaks[user_id]} wins in a row."
    if result["win"]:
        msg += f"\n🎉 {update.effective_user.full_name} cracked the code and wins! +10 XP."
        leaderboard = load_leaderboard()
        for uid in [session.player1_id, session.player2_id]:
            if str(uid) not in leaderboard:
                leaderboard[str(uid)] = {"xp": 0, "wins": 0}
        leaderboard[str(user_id)]["xp"] += 10 + result.get("streak_bonus", 0)
        leaderboard[str(user_id)]["wins"] += 1
        save_leaderboard(leaderboard)
        await update.message.reply_text(msg)
        del active_pvp_sessions[key]
        return
    elif session.is_ended():
        msg += "\nIt's a draw!"
        await update.message.reply_text(msg)
        del active_pvp_sessions[key]
        return
    # If extra_guess was just used, keep turn with this player
    if extra_guess_active:
        button = InlineKeyboardButton("You get an extra guess! Use /pvp_guess <1234>", callback_data="noop")
        markup = InlineKeyboardMarkup([[button]])
        await update.message.reply_text(f"<a href='tg://user?id={user_id}'>Your extra turn!</a>", reply_markup=markup, parse_mode="HTML")
    else:
        next_player = session.get_turn()
        button = InlineKeyboardButton("It's your turn! Guess with /pvp_guess <1234>", callback_data="noop")
        markup = InlineKeyboardMarkup([[button]])
        await update.message.reply_text(f"<a href='tg://user?id={next_player}'>Your turn!</a>", reply_markup=markup, parse_mode="HTML")

async def pvp_leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show PvP leaderboard (by XP and wins)."""
    leaderboard = load_leaderboard()
    if not leaderboard:
        await update.message.reply_text("No PvP games played yet.")
        return
    sorted_lb = sorted(leaderboard.items(), key=lambda x: (-x[1]["xp"], -x[1]["wins"]))
    msg = "🏆 PvP Leaderboard:\n"
    for i, (uid, stats) in enumerate(sorted_lb[:10], 1):
        msg += f"{i}. User {uid}: {stats['xp']} XP, {stats['wins']} Wins\n"
    await update.message.reply_text(msg)

async def pvp_rematch(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Allow both players to rematch after a game ends, keeping XP and wins."""
    user_id = update.effective_user.id
    # Find a session where this user is a participant
    key = None
    session = None
    for k, s in active_pvp_sessions.items():
        if user_id in k:
            key = k
            session = s
            break
    if not session:
        await update.message.reply_text("No active PvP game found.")
        return
    if not session.is_ended():
        await update.message.reply_text("Game is still in progress. Finish the current game first.")
        return
    session.rematch()
    await update.message.reply_text("Rematch started! Both players, please send /set_pvp_code <4 unique digits> in private chat with the bot.")

async def pvp_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show stats for both players in the current PvP session."""
    user_id = update.effective_user.id
    # Find a session where this user is a participant
    session = None
    for k, s in active_pvp_sessions.items():
        if user_id in k:
            session = s
            break
    if not session:
        await update.message.reply_text("No active PvP game found.")
        return
    stats = session.get_stats()
    msg = f"PvP Session Stats:\n"
    for pid, stat in stats.items():
        if pid == "games_played":
            msg += f"Games Played: {stat}\n"
        else:
            msg += f"User {pid}: {stat['xp']} XP, {stat['wins']} Wins, {stat['guesses']} Guesses\n"
    await update.message.reply_text(msg) 