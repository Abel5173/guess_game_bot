import logging
from telegram import Update
from telegram.ext import ContextTypes
from bot.game_manager import manager
from bot.pulse_code import PulseCodeGame

logger = logging.getLogger(__name__)


# --- Command Handlers ---
async def start_pulse_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    game = manager.start_pulse_code_game(
        chat_id, mode="architect", players=[user_id, -1], ai_personalities=["calculon"]
    )
    await update.message.reply_text(
        "💡 Pulse Code Architect Protocol started! Use /guess XXXX to make your first guess."
    )


async def start_dual_operative_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    if not context.args or not context.args[0].startswith("@"):
        await update.message.reply_text("Usage: /start_dual_operative_game @Player2")
        return
    player2_username = context.args[0][1:]
    player2_id = None
    for member in await update.effective_chat.get_administrators():
        if member.user.username == player2_username:
            player2_id = member.user.id
            break
    if not player2_id:
        await update.message.reply_text("Player2 not found in this chat.")
        return
    game = PulseCodeGame.setup_dual_operative(user_id, player2_id)
    manager.pulse_code_games[chat_id] = game
    await update.message.reply_text(
        f"Dual Operative Protocol initiated! <b>@{update.effective_user.username}</b> vs <b>@{player2_username}</b>. Each of you faces a unique AI. Use /guess @AI-Alpha XXXX or /guess @AI-Beta XXXX.",
        parse_mode="HTML",
    )


async def start_triple_threat_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    if not context.args or not context.args[0].startswith("@"):
        await update.message.reply_text("Usage: /start_triple_threat_game @Player2")
        return
    player2_username = context.args[0][1:]
    player2_id = None
    for member in await update.effective_chat.get_administrators():
        if member.user.username == player2_username:
            player2_id = member.user.id
            break
    if not player2_id:
        await update.message.reply_text("Player2 not found in this chat.")
        return
    game = PulseCodeGame.setup_triple_threat(user_id, player2_id)
    manager.pulse_code_games[chat_id] = game
    await update.message.reply_text(
        f"Triple Threat Protocol initiated! <b>@{update.effective_user.username}</b>, <b>@{player2_username}</b>, and Cipher-Bot are all in play. Use /guess @target XXXX to guess any code.",
        parse_mode="HTML",
    )


async def guess_pulse_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    game = manager.get_pulse_code_game(chat_id)
    if not game or not game.active:
        await update.message.reply_text(
            "No active Pulse Code game. Use /start_pulse_code to begin."
        )
        return
    if game.mode in ("dual", "triple"):
        if (
            len(context.args) != 2
            or not context.args[0].startswith("@")
            or len(context.args[1]) != 4
        ):
            await update.message.reply_text(
                "Usage: /guess @target XXXX (4 unique digits)"
            )
            return
        target_username = context.args[0][1:]
        guess = context.args[1]
        # Map username to user_id or AI id
        target_id = None
        for pid, pstate in game.players.items():
            if (
                pstate.is_ai
                and target_username.lower() in (pstate.ai_personality or "").lower()
            ):
                target_id = pid
            elif hasattr(update.effective_chat, "get_member"):
                try:
                    member = await update.effective_chat.get_member(pid)
                    if member.user.username == target_username:
                        target_id = pid
                except:
                    continue
        if not target_id:
            await update.message.reply_text("Target not found.")
            return
        result = game.make_guess(user_id, target_id, guess)
        if "error" in result:
            await update.message.reply_text(result["error"])
            return
        msg = f"@{update.effective_user.username} guessed {guess} against @{target_username}\nHits: {result['hits']}\nFlashes: {result['flashes']}\nStatic: {result['static']}\nStress: {result['stress']}%"
        if result["penalty"]:
            msg += f"\nPenalty: {result['penalty']}"
        if result["win"]:
            msg += f"\n🎉 @{update.effective_user.username} cracked the code!"
        if result.get("ai_feedback"):
            msg += f"\n{result['ai_feedback']}"
        await update.message.reply_text(msg)
        if result.get("ai_public"):
            await update.effective_chat.send_message(result["ai_public"])
        game.next_turn()
    else:
        # Architect mode
        if len(context.args) != 1 or len(context.args[0]) != 4:
            await update.message.reply_text("Usage: /guess XXXX (4 unique digits)")
            return
        guess = context.args[0]
        result = game.make_guess(user_id, -1, guess)
        if "error" in result:
            await update.message.reply_text(result["error"])
            return
        msg = f"Guess: {guess}\nHits: {result['hits']}\nFlashes: {result['flashes']}\nStatic: {result['static']}%"
        if result["penalty"]:
            msg += f"\nPenalty: {result['penalty']}"
        if result["win"]:
            msg += "\n🎉 You cracked the Pulse Code!"
        if result.get("ai_feedback"):
            msg += f"\n{result['ai_feedback']}"
        await update.message.reply_text(msg)
        if result.get("ai_public"):
            await update.effective_chat.send_message(result["ai_public"])


async def mind_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    game = manager.get_pulse_code_game(chat_id)
    if not game or not game.active:
        await update.message.reply_text("No active Pulse Code game.")
        return
    hint = game.use_mind_link(user_id, -1)
    await update.message.reply_text(f"Mind Link activated. Cryptic hint: {hint}")


async def desperation_gambit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    game = manager.get_pulse_code_game(chat_id)
    if not game or not game.active:
        await update.message.reply_text("No active Pulse Code game.")
        return
    if len(context.args) != 1 or len(context.args[0]) != 4:
        await update.message.reply_text(
            "Usage: /desperation_gambit XXXX (4 unique digits)"
        )
        return
    guess = context.args[0]
    result = game.desperation_gambit(user_id, -1, guess)
    if "error" in result:
        await update.message.reply_text(result["error"])
        return
    await update.message.reply_text(result["result"])


async def feedback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    game = manager.get_pulse_code_game(chat_id)
    if not game or not game.active:
        await update.message.reply_text("No active Pulse Code game.")
        return
    if len(context.args) != 3:
        await update.message.reply_text("Usage: /feedback [hits] [flashes] [static]")
        return
    try:
        hits = int(context.args[0])
        flashes = int(context.args[1])
        static = int(context.args[2])
    except ValueError:
        await update.message.reply_text("Feedback values must be integers.")
        return
    # For now, just acknowledge feedback (expand logic as needed)
    await update.message.reply_text(
        f"Feedback received: {hits} Hits, {flashes} Flashes, {static} Static."
    )


async def join_pulse_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    manager.join_pulse_code(chat_id, user_id)
    await update.message.reply_text(
        f"@{update.effective_user.username} joined the Pulse Code session!"
    )


async def leave_pulse_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    manager.leave_pulse_code(chat_id, user_id)
    await update.message.reply_text(
        f"@{update.effective_user.username} left the Pulse Code session."
    )


async def pulse_code_players(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    player_ids = manager.list_pulse_code_players(chat_id)
    if not player_ids:
        await update.message.reply_text("No players in this Pulse Code session.")
        return
    names = []
    for pid in player_ids:
        try:
            member = await update.effective_chat.get_member(pid)
            names.append(
                f"@{member.user.username}" if member.user.username else str(pid)
            )
        except:
            names.append(str(pid))
    await update.message.reply_text("Pulse Code Players: " + ", ".join(names))


async def pulse_code_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    game = manager.get_pulse_code_game(chat_id)
    if not game:
        await update.message.reply_text("No active Pulse Code game.")
        return
    status = game.get_status(user_id)
    player_ids = manager.list_pulse_code_players(chat_id)
    names = []
    for pid in player_ids:
        try:
            member = await update.effective_chat.get_member(pid)
            names.append(
                f"@{member.user.username}" if member.user.username else str(pid)
            )
        except:
            names.append(str(pid))
    turn_order = [
        (
            f"@{update.effective_chat.get_member(pid).user.username}"
            if hasattr(update.effective_chat.get_member(pid).user, "username")
            else str(pid)
        )
        for pid in game.turn_order
    ]
    msg = f"Your Stress: {status['stress']}%\nGuesses: {status['guesses']}\nMind Link used: {status['mind_link_used']}\nDesperation Gambit used: {status['gambit_used']}\n\nPlayers: {', '.join(names)}\nTurn Order: {', '.join(turn_order)}"
    await update.message.reply_text(msg)


async def end_pulse_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    manager.end_pulse_code_game(chat_id)
    await update.message.reply_text("Pulse Code game ended.")
