import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from bot.pulse_code_manager import pulse_code_game_manager, pulse_code_pvp_manager, pulse_code_group_ai_manager, pulse_code_group_pvp_manager
from bot.pulse_code import PulseCodeGame, AI_PERSONALITIES
from bot.game.pvp import PvPGameSession
from bot.decorators import game_is_active
from bot.player_stats import update_player_stats

logger = logging.getLogger(__name__)


async def start_pulse_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Sends a message with game mode options for Pulse-Code."""
    keyboard = [
        [InlineKeyboardButton("AI vs. Player", callback_data="pulse_mode_architect")],
        [InlineKeyboardButton("Player vs. Player", callback_data="pulse_mode_pvp")],
        [InlineKeyboardButton("Group vs. AI", callback_data="pulse_mode_group_ai")],
        [InlineKeyboardButton("Group vs. Group", callback_data="pulse_mode_group_pvp")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.callback_query:
        await update.callback_query.edit_message_text(
            "Select a Pulse-Code game mode:", reply_markup=reply_markup
        )
    else:
        await update.message.reply_text(
            "Select a Pulse-Code game mode:", reply_markup=reply_markup
        )


async def handle_pulse_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles all callback queries for Pulse Code games."""
    query = update.callback_query
    await query.answer()
    data = query.data
    chat_id = query.message.chat_id
    user_id = query.from_user.id

    if data == "pulse_mode_architect":
        keyboard = [
            [
                InlineKeyboardButton(
                    name.capitalize(), callback_data=f"pulse_start_architect_{name}"
                )
                for name in AI_PERSONALITIES.keys()
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            "Choose your AI opponent for Architect mode:", reply_markup=reply_markup
        )

    elif data.startswith("pulse_start_architect_"):
        ai_personality = data.replace("pulse_start_architect_", "")
        game = PulseCodeGame.setup_architect(user_id, ai_personality)
        pulse_code_game_manager.new_game(chat_id, game)
        await query.edit_message_text(
            text=f"💡 Pulse Code Architect Protocol started against {ai_personality.capitalize()}!\n"
            f"Your target is the AI. Use `/guess <code>` to find their 4-digit code.\n"
            f"Example: `/guess 1234`"
        )
    
    elif data == "pulse_mode_pvp":
        # PvP lobby creation/joining
        game = pulse_code_pvp_manager.get_game(chat_id)
        if not game:
            pulse_code_pvp_manager.new_game(chat_id, user_id)
            keyboard = [[InlineKeyboardButton("Join as Player 2", callback_data="pvp_join")]]
            await query.edit_message_text(
                text="PvP lobby created! Waiting for Player 2 to join...",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        elif game.players[1] is None and user_id != game.players[0]:
            pulse_code_pvp_manager.join_game(chat_id, user_id)
            await query.edit_message_text(
                text="Both players joined! Each player, please set your secret code using /set_code <4-unique-digits> in this chat.",
                reply_markup=None
            )
        else:
            await query.edit_message_text(
                text="PvP lobby is full or you are already in the game.",
                reply_markup=None
            )
    elif data == "pvp_join":
        game = pulse_code_pvp_manager.get_game(chat_id)
        if game and game.players[1] is None and user_id != game.players[0]:
            pulse_code_pvp_manager.join_game(chat_id, user_id)
            await query.edit_message_text(
                text="Both players joined! Each player, please set your secret code using /set_code <4-unique-digits> in this chat.",
                reply_markup=None
            )
        else:
            await query.edit_message_text(
                text="PvP lobby is full or you are already in the game.",
                reply_markup=None
            )
    elif data == "pulse_mode_group_ai":
        # Group vs. AI lobby creation/joining
        game = pulse_code_group_ai_manager.get_game(chat_id)
        if not game:
            pulse_code_group_ai_manager.new_game(chat_id)
            keyboard = [[InlineKeyboardButton("Join Group", callback_data="group_ai_join")]]
            await query.edit_message_text(
                text="Group vs. AI lobby created! Players, click below to join.",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        else:
            await query.edit_message_text(
                text="Group vs. AI lobby already exists. Players, click below to join.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Join Group", callback_data="group_ai_join")]])
            )
    elif data == "group_ai_join":
        game = pulse_code_group_ai_manager.get_game(chat_id)
        if not game:
            await query.edit_message_text("No active Group vs. AI lobby. Please start again.")
            return
        if user_id in game.players:
            await query.edit_message_text("You have already joined the group.")
            return
        game.add_player(user_id)
        await query.edit_message_text(f"Player {user_id} joined! Current players: {len(game.players)}. Use /start_group_ai when ready.", reply_markup=None)
    elif data == "group_ai_select_ai":
        # Show AI personalities to select
        keyboard = [[InlineKeyboardButton(name.capitalize(), callback_data=f"group_ai_start_{name}") for name in AI_PERSONALITIES.keys()]]
        await query.edit_message_text("Choose your AI opponent for Group vs. AI:", reply_markup=InlineKeyboardMarkup(keyboard))
    elif data.startswith("group_ai_start_"):
        ai_personality = data.replace("group_ai_start_", "")
        game = pulse_code_group_ai_manager.get_game(chat_id)
        if not game or len(game.players) < 2:
            await query.edit_message_text("Not enough players to start. At least 2 required.")
            return
        from bot.pulse_code import generate_pulse_code
        ai_code = generate_pulse_code()
        game.set_ai(ai_personality, ai_code)
        await query.edit_message_text(f"💡 Group vs. AI started against {ai_personality.capitalize()}! Player {game.get_current_player()} goes first. Use /group_guess <code>.")

    elif data == "pulse_mode_group_pvp":
        # Group vs. Group lobby creation/joining
        game = pulse_code_group_pvp_manager.get_game(chat_id)
        if not game:
            pulse_code_group_pvp_manager.new_game(chat_id)
            keyboard = [
                [InlineKeyboardButton("Join Team A", callback_data="group_pvp_join_a"),
                 InlineKeyboardButton("Join Team B", callback_data="group_pvp_join_b")]
            ]
            await query.edit_message_text(
                text="Group vs. Group lobby created! Players, click below to join a team.",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        else:
            await query.edit_message_text(
                text="Group vs. Group lobby already exists. Players, click below to join a team.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("Join Team A", callback_data="group_pvp_join_a"),
                     InlineKeyboardButton("Join Team B", callback_data="group_pvp_join_b")]
                ])
            )
    elif data == "group_pvp_join_a":
        game = pulse_code_group_pvp_manager.get_game(chat_id)
        if not game:
            await query.edit_message_text("No active Group vs. Group lobby. Please start again.")
            return
        if user_id in game.teams["A"] or user_id in game.teams["B"]:
            await query.edit_message_text("You have already joined a team.")
            return
        game.add_player("A", user_id)
        await query.edit_message_text(f"Player {user_id} joined Team A! Use /set_team_code <code> if you are the code setter. Use /start_group_pvp when both teams are ready.", reply_markup=None)
    elif data == "group_pvp_join_b":
        game = pulse_code_group_pvp_manager.get_game(chat_id)
        if not game:
            await query.edit_message_text("No active Group vs. Group lobby. Please start again.")
            return
        if user_id in game.teams["A"] or user_id in game.teams["B"]:
            await query.edit_message_text("You have already joined a team.")
            return
        game.add_player("B", user_id)
        await query.edit_message_text(f"Player {user_id} joined Team B! Use /set_team_code <code> if you are the code setter. Use /start_group_pvp when both teams are ready.", reply_markup=None)


@game_is_active
async def guess_pulse_code(update: Update, context: ContextTypes.DEFAULT_TYPE, game: PulseCodeGame):
    user_id = update.effective_user.id
    username = update.effective_user.username or "player"

    if not context.args or len(context.args[0]) != 4 or not context.args[0].isdigit():
        await update.message.reply_text("Invalid guess. Use `/guess XXXX` with 4 unique digits.")
        return

    guess = context.args[0]
    if len(set(guess)) != 4:
        await update.message.reply_text("Your guess must contain 4 unique digits.")
        return

    target_id = game.ai_targets.get(user_id)
    if target_id is None:
        await update.message.reply_text("Could not determine your target.")
        return

    result = game.make_guess(user_id, target_id, guess, username)

    if "error" in result:
        await update.message.reply_text(result["error"])
        return

    response_lines = [
        f"Guesser: @{username}",
        f"Target: AI ({game.players[target_id].ai_personality.capitalize()})",
        f"Guess: `{guess}`",
        "---"
        f"Hits: {result['hits']} | Flashes: {result['flashes']} | Static: {result['static']}",
        f"Your Stress: {result['stress']}%",
    ]

    if result.get("penalty"):
        response_lines.append(f"Penalty: {result['penalty']}")

    if result.get("ai_feedback"):
        response_lines.append(f"AI Feedback: {result['ai_feedback']}")

    if result["win"]:
        xp_gain = 50
        update_player_stats(user_id, xp_gain=xp_gain, won=True)
        response_lines.append(f"\n🎉 Congratulations, @{username}! You've cracked the code and earned {xp_gain} XP!")
        pulse_code_game_manager.end_game(update.effective_chat.id)
    
    await update.message.reply_text("\n".join(response_lines), parse_mode="Markdown")

    if result.get("ai_public"):
        await update.effective_chat.send_message(result["ai_public"])


@game_is_active
async def pulse_code_status(update: Update, context: ContextTypes.DEFAULT_TYPE, game: PulseCodeGame):
    user_id = update.effective_user.id
    player_state = game.get_status(user_id)
    if not player_state:
        await update.message.reply_text("You are not a player in the current game.")
        return

    status_message = (
        f"**Your Pulse Code Status**\n"
        f"Stress Level: `{player_state['stress']}%`\n"
        f"Guesses Made: `{len(player_state['guesses'])}`\n"
        f"Previous Guesses: `{', '.join(player_state['guesses'])}`\n"
        f"Mind Link Used: `{'Yes' if player_state['mind_link_used'] else 'No'}`\n"
        f"Desperation Gambit Used: `{'Yes' if player_state['gambit_used'] else 'No'}`"
    )
    await update.message.reply_text(status_message, parse_mode="Markdown")


@game_is_active
async def end_pulse_code(update: Update, context: ContextTypes.DEFAULT_TYPE, game: PulseCodeGame):
    pulse_code_game_manager.end_game(update.effective_chat.id)
    await update.message.reply_text("Pulse Code game has been successfully ended.")


# Placeholder for other commands
async def mind_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Mind Link functionality is coming soon!")

async def desperation_gambit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Desperation Gambit functionality is coming soon!")
    
async def feedback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Feedback functionality is coming soon!")

async def join_pulse_code(update: Update, context:ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Join Pulse Code functionality is coming soon!")

async def leave_pulse_code(update: Update, context:ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Leave Pulse Code functionality is coming soon!")

async def pulse_code_players(update: Update, context:ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Pulse Code Players functionality is coming soon!")

async def start_dual_operative_game(update: Update, context:ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Start Dual Operative Game functionality is coming soon!")

async def start_triple_threat_game(update: Update, context:ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Start Triple Threat Game functionality is coming soon!")

# PvP Handlers
async def join_pvp(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    game = pulse_code_pvp_manager.get_game(chat_id)
    if not game:
        pulse_code_pvp_manager.new_game(chat_id, user_id)
        await update.message.reply_text("PvP lobby created! Waiting for Player 2 to join...")
    elif game.players[1] is None and user_id != game.players[0]:
        pulse_code_pvp_manager.join_game(chat_id, user_id)
        await update.message.reply_text("Both players joined! Each player, please set your secret code using /set_code <4-unique-digits> in this chat.")
    else:
        await update.message.reply_text("PvP lobby is full or you are already in the game.")

async def set_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    game = pulse_code_pvp_manager.get_game(chat_id)
    if not game or user_id not in game.players:
        await update.message.reply_text("You are not in an active PvP game.")
        return
    if not context.args or len(context.args[0]) != 4 or not context.args[0].isdigit() or len(set(context.args[0])) != 4:
        await update.message.reply_text("Invalid code. Use /set_code <4-unique-digits>.")
        return
    success = game.set_code(user_id, context.args[0])
    if not success:
        await update.message.reply_text("Invalid or duplicate code. Try again.")
        return
    await update.message.reply_text("Code set! Waiting for the other player.")
    if len(game.codes) == 2:
        await update.message.reply_text(f"Both codes set! {game.current_player()} goes first. Use /pvp_guess <4-unique-digits> to guess.")

async def pvp_guess(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    game = pulse_code_pvp_manager.get_game(chat_id)
    if not game or user_id not in game.players:
        await update.message.reply_text("You are not in an active PvP game.")
        return
    if not context.args or len(context.args[0]) != 4 or not context.args[0].isdigit() or len(set(context.args[0])) != 4:
        await update.message.reply_text("Invalid guess. Use /pvp_guess <4-unique-digits>.")
        return
    result = game.make_guess(user_id, context.args[0])
    if "error" in result:
        await update.message.reply_text(result["error"])
        return
    await update.message.reply_text(f"Guess: {context.args[0]} | Hits: {result['exact']} | Flashes: {result['misplaced']}")
    if result["win"]:
        await update.message.reply_text(f"🎉 Player {user_id} wins! Game over.")
        pulse_code_pvp_manager.end_game(chat_id)
    else:
        await update.message.reply_text(f"Next turn: Player {game.current_player()}")

async def pvp_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    game = pulse_code_pvp_manager.get_game(chat_id)
    if not game or user_id not in game.players:
        await update.message.reply_text("You are not in an active PvP game.")
        return
    guesses = game.guesses[user_id]
    await update.message.reply_text(f"Your guesses: {guesses}\nYour code: {'SET' if user_id in game.codes else 'NOT SET'}\nCurrent turn: Player {game.current_player()}")

async def end_pvp(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    game = pulse_code_pvp_manager.get_game(chat_id)
    if not game:
        await update.message.reply_text("No active PvP game to end.")
        return
    pulse_code_pvp_manager.end_game(chat_id)
    await update.message.reply_text("PvP game ended.")

# Group vs. AI Handlers
async def join_group_ai(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    game = pulse_code_group_ai_manager.get_game(chat_id)
    if not game:
        pulse_code_group_ai_manager.new_game(chat_id)
        game = pulse_code_group_ai_manager.get_game(chat_id)
    if user_id in game.players:
        await update.message.reply_text("You have already joined the group.")
        return
    game.add_player(user_id)
    await update.message.reply_text(f"Player {user_id} joined! Current players: {len(game.players)}. Use /start_group_ai when ready.")

async def start_group_ai(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    game = pulse_code_group_ai_manager.get_game(chat_id)
    if not game or len(game.players) < 2:
        await update.message.reply_text("Not enough players to start. At least 2 required.")
        return
    # Show AI personalities to select
    keyboard = [[InlineKeyboardButton(name.capitalize(), callback_data=f"group_ai_start_{name}") for name in AI_PERSONALITIES.keys()]]
    await update.message.reply_text("Choose your AI opponent for Group vs. AI:", reply_markup=InlineKeyboardMarkup(keyboard))

async def group_guess(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    game = pulse_code_group_ai_manager.get_game(chat_id)
    if not game or not game.active:
        await update.message.reply_text("No active Group vs. AI game.")
        return
    if not game.is_player(user_id):
        await update.message.reply_text("You are not a player in this game.")
        return
    if user_id != game.get_current_player():
        await update.message.reply_text("It's not your turn.")
        return
    if not context.args or len(context.args[0]) != 4 or not context.args[0].isdigit() or len(set(context.args[0])) != 4:
        await update.message.reply_text("Invalid guess. Use /group_guess <4-unique-digits>.")
        return
    result = game.make_guess(user_id, context.args[0])
    if "error" in result:
        await update.message.reply_text(result["error"])
        return
    response_lines = [
        f"Guesser: {user_id}",
        f"Guess: `{context.args[0]}`",
        f"Hits: {result['hits']} | Flashes: {result['flashes']} | Static: {result['static']}",
        f"Your Stress: {result['stress']}%",
    ]
    if result.get("penalty"):
        response_lines.append(f"Penalty: {result['penalty']}")
    if result["win"]:
        response_lines.append(f"\n🎉 Congratulations, Player {user_id}! You've cracked the code!")
        pulse_code_group_ai_manager.end_game(chat_id)
    else:
        game.next_turn()
        response_lines.append(f"Next turn: Player {game.get_current_player()}")
    await update.message.reply_text("\n".join(response_lines))

async def group_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    game = pulse_code_group_ai_manager.get_game(chat_id)
    if not game or not game.is_player(user_id):
        await update.message.reply_text("You are not a player in this game.")
        return
    status = game.get_status(user_id)
    if not status:
        await update.message.reply_text("No status found.")
        return
    await update.message.reply_text(
        f"Your Stress: {status['stress']}%\nGuesses: {', '.join(status['guesses'])}\nPenalties: {', '.join(status['penalties'])}\nYour Turn: {'Yes' if status['turn'] else 'No'}"
    )

async def end_group_ai(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    game = pulse_code_group_ai_manager.get_game(chat_id)
    if not game:
        await update.message.reply_text("No active Group vs. AI game to end.")
        return
    pulse_code_group_ai_manager.end_game(chat_id)
    await update.message.reply_text("Group vs. AI game ended.")

# Group vs. Group Handlers
async def join_team_a(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    game = pulse_code_group_pvp_manager.get_game(chat_id)
    if not game:
        pulse_code_group_pvp_manager.new_game(chat_id)
        game = pulse_code_group_pvp_manager.get_game(chat_id)
    if user_id in game.teams["A"] or user_id in game.teams["B"]:
        await update.message.reply_text("You have already joined a team.")
        return
    game.add_player("A", user_id)
    await update.message.reply_text(f"Player {user_id} joined Team A! Use /set_team_code <code> if you are the code setter. Use /start_group_pvp when both teams are ready.")

async def join_team_b(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    game = pulse_code_group_pvp_manager.get_game(chat_id)
    if not game:
        pulse_code_group_pvp_manager.new_game(chat_id)
        game = pulse_code_group_pvp_manager.get_game(chat_id)
    if user_id in game.teams["A"] or user_id in game.teams["B"]:
        await update.message.reply_text("You have already joined a team.")
        return
    game.add_player("B", user_id)
    await update.message.reply_text(f"Player {user_id} joined Team B! Use /set_team_code <code> if you are the code setter. Use /start_group_pvp when both teams are ready.")

async def set_team_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    game = pulse_code_group_pvp_manager.get_game(chat_id)
    if not game or not (user_id in game.teams["A"] or user_id in game.teams["B"]):
        await update.message.reply_text("You are not in an active Group vs. Group game.")
        return
    team = "A" if user_id in game.teams["A"] else "B"
    if not context.args or len(context.args[0]) != 4 or not context.args[0].isdigit() or len(set(context.args[0])) != 4:
        await update.message.reply_text("Invalid code. Use /set_team_code <4-unique-digits>.")
        return
    success = game.set_code(team, context.args[0])
    if not success:
        await update.message.reply_text("Invalid or duplicate code. Try again.")
        return
    await update.message.reply_text(f"Team {team} code set! Waiting for the other team.")
    if game.can_start():
        await update.message.reply_text(f"Both codes set! Team {game.get_current_team()} goes first. Use /team_guess <4-unique-digits> to guess.")

async def start_group_pvp(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    game = pulse_code_group_pvp_manager.get_game(chat_id)
    if not game or not game.can_start():
        await update.message.reply_text("Both teams must have at least one player and set their code to start.")
        return
    game.start()
    await update.message.reply_text(f"Group vs. Group started! Team {game.get_current_team()} goes first. Use /team_guess <4-unique-digits> to guess.")

async def team_guess(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    game = pulse_code_group_pvp_manager.get_game(chat_id)
    if not game or not game.active:
        await update.message.reply_text("No active Group vs. Group game.")
        return
    team = None
    if user_id in game.teams["A"]:
        team = "A"
    elif user_id in game.teams["B"]:
        team = "B"
    else:
        await update.message.reply_text("You are not a player in this game.")
        return
    if team != game.get_current_team():
        await update.message.reply_text("It's not your team's turn.")
        return
    if not context.args or len(context.args[0]) != 4 or not context.args[0].isdigit() or len(set(context.args[0])) != 4:
        await update.message.reply_text("Invalid guess. Use /team_guess <4-unique-digits>.")
        return
    result = game.make_guess(team, context.args[0], user_id)
    if "error" in result:
        await update.message.reply_text(result["error"])
        return
    response_lines = [
        f"Team: {team}",
        f"Guesser: {user_id}",
        f"Guess: `{context.args[0]}`",
        f"Hits: {result['hits']} | Flashes: {result['flashes']} | Static: {result['static']}",
        f"Your Stress: {result['stress']}%",
    ]
    if result.get("penalty"):
        response_lines.append(f"Penalty: {result['penalty']}")
    if result["win"]:
        response_lines.append(f"\n🎉 Congratulations, Team {team}! You've cracked the code!")
        pulse_code_group_pvp_manager.end_game(chat_id)
    else:
        game.next_turn()
        response_lines.append(f"Next turn: Team {game.get_current_team()}")
    await update.message.reply_text("\n".join(response_lines))

async def team_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    game = pulse_code_group_pvp_manager.get_game(chat_id)
    if not game:
        await update.message.reply_text("No active Group vs. Group game.")
        return
    team = None
    if user_id in game.teams["A"]:
        team = "A"
    elif user_id in game.teams["B"]:
        team = "B"
    else:
        await update.message.reply_text("You are not a player in this game.")
        return
    status = game.get_status(team, user_id)
    if not status:
        await update.message.reply_text("No status found.")
        return
    await update.message.reply_text(
        f"Your Stress: {status['stress']}%\nGuesses: {', '.join(status['guesses'])}\nPenalties: {', '.join(status['penalties'])}\nYour Team's Turn: {'Yes' if status['turn'] else 'No'}"
    )

async def end_group_pvp(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    game = pulse_code_group_pvp_manager.get_game(chat_id)
    if not game:
        await update.message.reply_text("No active Group vs. Group game to end.")
        return
    pulse_code_group_pvp_manager.end_game(chat_id)
    await update.message.reply_text("Group vs. Group game ended.")
