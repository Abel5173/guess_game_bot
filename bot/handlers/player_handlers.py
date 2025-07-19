import logging
from telegram import Update
from telegram.ext import ContextTypes
from bot.player_stats import get_player_stats, get_leaderboard

logger = logging.getLogger(__name__)

async def show_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Displays the user's own profile and stats."""
    user_id = update.effective_user.id
    stats = get_player_stats(user_id)

    if not stats:
        await update.message.reply_text("You don't have a profile yet. Play a game to create one!")
        return

    profile_message = (
        f"**Your Profile**\n\n"
        f"Level: `{stats['level']}`\n"
        f"XP: `{stats['xp']}`\n"
        f"Games Played: `{stats['games_played']}`\n"
        f"Wins: `{stats['wins']}`\n"
        f"Losses: `{stats['losses']}`"
    )
    await update.message.reply_text(profile_message, parse_mode="Markdown")


async def show_leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Displays the global leaderboard."""
    leaderboard = get_leaderboard()

    if not leaderboard:
        await update.message.reply_text("The leaderboard is empty. Be the first to play!")
        return

    leaderboard_message = "**Global Leaderboard**\n\n"
    for i, (user_id, xp, level) in enumerate(leaderboard):
        # Attempt to get username, fallback to user_id
        try:
            user = await context.bot.get_chat(user_id)
            username = f"@{user.username}" if user.username else user.full_name
        except Exception:
            username = f"User ID: {user_id}"
        
        leaderboard_message += f"{i+1}. {username} - Level {level} ({xp} XP)\n"

    await update.message.reply_text(leaderboard_message)
