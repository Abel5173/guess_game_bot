from telegram import InlineKeyboardMarkup, InlineKeyboardButton

def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🕹️ Start New Game", callback_data="startgame")],
        [InlineKeyboardButton("🏆 View Leaderboard", callback_data="leaderboard")],
        [InlineKeyboardButton("📄 My Profile", callback_data="profile")],
    ])

def lobby_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🙋 Join Game", callback_data="join_impostor")],
        [InlineKeyboardButton("🚦 Start Game", callback_data="start_impostor")],
        [InlineKeyboardButton("📊 Status", callback_data="show_status")],
    ])

def voting_menu(alive_players):
    return InlineKeyboardMarkup(
        [[InlineKeyboardButton(f"🚀 Vote {p['name']} {p.get('title','')}", callback_data=f"vote_{uid}")]
         for uid, p in alive_players.items()] +
        [[InlineKeyboardButton("🛑 Skip Vote", callback_data="vote_skip")]]
    )

def profile_card(player):
    return (
        f"📄 <b>Profile</b> — {player.name}\n"
        f"🏷️ Title: <code>{player.title}</code>\n"
        f"✨ XP: <b>{player.xp}</b>\n"
        f"🔧 Tasks Done: {player.tasks_done}\n"
        f"🛠️ Faked Tasks: {player.fake_tasks_done}"
    )

def leaderboard_card(top_players):
    medals = ["🥇", "🥈", "🥉"] + ["🏅"]*7
    lines = [f"🏆 <b>Leaderboard</b> — Top Players"]
    for i, p in enumerate(top_players, start=1):
        medal = medals[i-1] if i <= len(medals) else ""
        lines.append(f"{medal} {i}. {p.name} — {p.xp} XP ({p.title})")
    return "\n".join(lines)

def celebration_win():
    return "🎉 <b>Victory!</b>"

def celebration_lose():
    return "💀 <b>Defeat!</b>" 