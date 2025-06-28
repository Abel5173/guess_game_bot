from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def main_menu():
    """Main menu with core actions."""
    keyboard = [
        [InlineKeyboardButton("👤 Profile", callback_data="show_profile")],
        [InlineKeyboardButton("✅ Complete Task", callback_data="complete_task")],
        [InlineKeyboardButton("📊 Leaderboard", callback_data="show_leaderboard")],
        [InlineKeyboardButton("📖 Rules", callback_data="show_rules")],
        [InlineKeyboardButton("🕵️ Start Discussion", callback_data="start_discussion")],
        [InlineKeyboardButton("🗳️ Voting Phase", callback_data="start_voting")],
        [InlineKeyboardButton("❌ End Game", callback_data="end_game")]
    ]
    return InlineKeyboardMarkup(keyboard)


def voting_menu(alive_players):
    """
    Creates a voting menu with buttons for each alive player plus skip vote.

    Args:
        alive_players (dict): user_id to player_name mapping of alive players.

    Returns:
        InlineKeyboardMarkup: Voting buttons markup.
    """
    keyboard = [[InlineKeyboardButton(name,
                                      callback_data=f"vote_{user_id}")] for user_id,
                name in alive_players.items()]
    keyboard.append([InlineKeyboardButton(
        "⏭️ Skip Vote", callback_data="vote_skip")])
    return InlineKeyboardMarkup(keyboard)


def join_game_menu():
    """Buttons for joining and starting the impostor game."""
    keyboard = [
        [InlineKeyboardButton("🙋 Join Impostor Game", callback_data="join_impostor")],
        [InlineKeyboardButton("🚦 Start Impostor Game", callback_data="start_impostor")]
    ]
    return InlineKeyboardMarkup(keyboard)


def confirm_end_game():
    """Confirm end game menu."""
    keyboard = [
        [InlineKeyboardButton("✅ Yes, End Game", callback_data="confirm_end_game")],
        [InlineKeyboardButton("❌ Cancel", callback_data="cancel_end_game")]
    ]
    return InlineKeyboardMarkup(keyboard)
