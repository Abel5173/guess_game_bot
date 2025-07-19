import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from bot.pulse_code import PulseCodeGame, PulseAIPersonality, AI_PERSONALITIES
from bot.pulse_code_manager import pulse_code_game_manager
from bot.handlers.pulse_code_handlers import (
    start_pulse_code,
    handle_pulse_callback,
    guess_pulse_code,
    pulse_code_status,
    end_pulse_code,
)

# Mock the LLM service to prevent actual API calls


# Mock player stats update
@pytest.fixture(autouse=True)
def mock_player_stats():
    with patch("bot.player_stats.update_player_stats", return_value=None) as mock:
        yield mock

@pytest.fixture
def mock_update():
    update = MagicMock(spec=Update)
    update.effective_chat.id = 12345
    update.effective_chat.send_message = AsyncMock() # Make send_message awaitable
    update.effective_user.id = 67890
    update.effective_user.username = "test_user"
    update.message = AsyncMock()
    update.message.chat_id = update.effective_chat.id # Ensure message has chat_id
    update.callback_query = AsyncMock()
    update.callback_query.from_user.id = update.effective_user.id # Ensure callback user ID matches effective user ID
    return update

@pytest.fixture
def mock_context():
    context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
    context.args = []
    return context

@pytest.mark.asyncio
async def test_pulse_code_full_integration(mock_update, mock_context):
    chat_id = mock_update.effective_chat.id
    user_id = mock_update.effective_user.id
    username = mock_update.effective_user.username

    # 1. Test start_pulse_code (initial message, no callback)
    mock_update.callback_query = None # Ensure no callback for initial call
    await start_pulse_code(mock_update, mock_context)
    mock_update.message.reply_text.assert_called_once()
    args, kwargs = mock_update.message.reply_text.call_args
    assert "Select a Pulse-Code game mode:" in args[0]
    assert isinstance(kwargs["reply_markup"], InlineKeyboardMarkup)

    # Simulate callback for "AI vs. Player"
    mock_update.callback_query = AsyncMock() # Now simulate a callback
    mock_update.callback_query.data = "pulse_mode_architect"
    mock_update.callback_query.message = mock_update.message # Callback needs a message to edit
    await handle_pulse_callback(mock_update, mock_context)
    mock_update.callback_query.edit_message_text.assert_called_once()
    args, kwargs = mock_update.callback_query.edit_message_text.call_args
    assert "Choose your AI opponent for Architect mode:" in args[0]
    assert isinstance(kwargs["reply_markup"], InlineKeyboardMarkup)

    # Simulate callback for starting game with "Calculon" AI
    with patch.object(mock_update.callback_query.from_user, 'id', new=user_id):
        mock_update.callback_query.data = "pulse_start_architect_calculon"
        await handle_pulse_callback(mock_update, mock_context)
    mock_update.callback_query.edit_message_text.assert_called_with(
        text=f"""💡 Pulse Code Architect Protocol started against Calculon!
Your target is the AI. Use `/guess <code>` to find their 4-digit code.
Example: `/guess 1234`"""
    )
    assert pulse_code_game_manager.get_game(chat_id) is not None
    game = pulse_code_game_manager.get_game(chat_id)
    assert game.mode == "architect"
    assert user_id in game.players
    assert -1 in game.players # AI player
    assert game.players[-1].ai_personality == "calculon"

    # Store the AI's code for testing purposes (normally hidden)
    ai_code = game.players[-1].code
    print(f"AI's secret code: {ai_code}") # For debugging test failures

    # 2. Test guess_pulse_code - Invalid guess
    mock_update.message = AsyncMock() # Reset mock for new message
    await guess_pulse_code(mock_update, mock_context)
    mock_update.message.reply_text.assert_called_with("Invalid guess. Use `/guess XXXX` with 4 unique digits.")

    mock_context.args = ["1123"] # Non-unique digits
    mock_update.message = AsyncMock() # Reset mock for new message
    await guess_pulse_code(mock_update, mock_context)
    mock_update.message.reply_text.assert_called_with("Your guess must contain 4 unique digits.")

    # 3. Test guess_pulse_code - Correct guess (winning)
    mock_update.message = AsyncMock() # Reset mock for new message
    mock_context.args = [ai_code] # The correct code
    await guess_pulse_code(mock_update, mock_context)
    
    mock_update.message.reply_text.assert_called_once()
    reply_text_call_args = mock_update.message.reply_text.call_args[0][0]
    assert f"🎉 Congratulations, @{username}! You've cracked the code and earned 50 XP!" in reply_text_call_args
    assert "Hits: 4 | Flashes: 0 | Static: 0" in reply_text_call_args
    assert not game.active # Game should be ended
    assert pulse_code_game_manager.get_game(chat_id) is None # Game should be removed from manager

    # Re-start game for status and end game tests
    mock_update.callback_query.data = "pulse_start_architect_maverick"
    mock_update.callback_query.from_user.id = user_id  # Ensure correct user ID
    await handle_pulse_callback(mock_update, mock_context)
    game = pulse_code_game_manager.get_game(chat_id)
    assert game is not None
    
    # Make a few incorrect guesses to build up state
    mock_context.args = ["1234"]
    mock_update.effective_user = MagicMock()
    mock_update.effective_user.id = user_id
    mock_update.effective_user.username = username
    mock_update.message = AsyncMock()
    await guess_pulse_code(mock_update, mock_context)
    mock_context.args = ["5678"]
    mock_update.effective_user = MagicMock()
    mock_update.effective_user.id = user_id
    mock_update.effective_user.username = username
    mock_update.message = AsyncMock()
    await guess_pulse_code(mock_update, mock_context)

    # 4. Test pulse_code_status
    print(f"DEBUG: user_id={user_id}, game.players.keys()={list(game.players.keys())}")
    mock_update.message = AsyncMock()
    await pulse_code_status(mock_update, mock_context)  # Removed 'game' argument
    mock_update.message.reply_text.assert_called_once()
    status_message = mock_update.message.reply_text.call_args[0][0]
    assert "**Your Pulse Code Status**" in status_message
    assert "Guesses Made: `2`" in status_message
    assert "Previous Guesses: `1234, 5678`" in status_message # Assuming these were the guesses

    # 5. Test end_pulse_code
    mock_update.message = AsyncMock()
    await end_pulse_code(mock_update, mock_context)  # Removed 'game' argument
    mock_update.message.reply_text.assert_called_once_with("Pulse Code game has been successfully ended.")
    assert pulse_code_game_manager.get_game(chat_id) is None

@pytest.mark.asyncio
async def test_pvp_full_flow():
    from bot.handlers.pulse_code_handlers import join_pvp, set_code, pvp_guess, pvp_status, end_pvp
    from bot.pulse_code_manager import pulse_code_pvp_manager
    from telegram.ext import ContextTypes
    from unittest.mock import MagicMock, AsyncMock

    chat_id = 54321
    player1_id = 1001
    player2_id = 1002
    username1 = "player1"
    username2 = "player2"

    # Setup mock context
    context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
    context.args = []

    # Player 1 joins PvP
    update1 = MagicMock()
    update1.effective_chat.id = chat_id
    update1.effective_user.id = player1_id
    update1.effective_user.username = username1
    update1.message = AsyncMock()
    await join_pvp(update1, context)
    update1.message.reply_text.assert_called_with("PvP lobby created! Waiting for Player 2 to join...")

    # Player 2 joins PvP
    update2 = MagicMock()
    update2.effective_chat.id = chat_id
    update2.effective_user.id = player2_id
    update2.effective_user.username = username2
    update2.message = AsyncMock()
    await join_pvp(update2, context)
    update2.message.reply_text.assert_called_with("Both players joined! Each player, please set your secret code using /set_code <4-unique-digits> in this chat.")

    # Player 1 sets code
    context.args = ["1234"]
    update1.message = AsyncMock()
    await set_code(update1, context)
    update1.message.reply_text.assert_called_with("Code set! Waiting for the other player.")

    # Player 2 sets code
    context.args = ["5678"]
    update2.message = AsyncMock()
    await set_code(update2, context)
    update2.message.reply_text.assert_any_call("Code set! Waiting for the other player.")
    update2.message.reply_text.assert_any_call(f"Both codes set! {player1_id} goes first. Use /pvp_guess <4-unique-digits> to guess.")

    # Player 1 makes a wrong guess
    context.args = ["8765"]
    update1.message = AsyncMock()
    await pvp_guess(update1, context)
    print("CALLS after player 1 guess:", update1.message.reply_text.call_args_list)
    update1.message.reply_text.assert_any_call("Guess: 8765 | Hits: 0 | Flashes: 4")
    update1.message.reply_text.assert_any_call(f"Next turn: Player {player2_id}")

    # Player 2 makes a wrong guess
    context.args = ["4321"]
    update2.message = AsyncMock()
    await pvp_guess(update2, context)
    update2.message.reply_text.assert_any_call("Guess: 4321 | Hits: 0 | Flashes: 4")
    update2.message.reply_text.assert_any_call(f"Next turn: Player {player1_id}")

    # Player 1 makes the winning guess
    context.args = ["5678"]
    update1.message = AsyncMock()
    await pvp_guess(update1, context)
    update1.message.reply_text.assert_any_call("Guess: 5678 | Hits: 4 | Flashes: 0")
    update1.message.reply_text.assert_any_call(f"🎉 Player {player1_id} wins! Game over.")

    # Game should be ended
    game = pulse_code_pvp_manager.get_game(chat_id)
    assert game is None

    # Try status after game ended
    update1.message = AsyncMock()
    await pvp_status(update1, context)
    update1.message.reply_text.assert_called_with("You are not in an active PvP game.")

    # Try ending a non-existent game
    update1.message = AsyncMock()
    await end_pvp(update1, context)
    update1.message.reply_text.assert_called_with("No active PvP game to end.")

@pytest.mark.asyncio
async def test_group_vs_ai_full_flow():
    from bot.handlers.pulse_code_handlers import join_group_ai, start_group_ai, group_guess, group_status, end_group_ai
    from bot.pulse_code_manager import pulse_code_group_ai_manager
    from telegram.ext import ContextTypes
    from unittest.mock import MagicMock, AsyncMock
    from bot.pulse_code import generate_pulse_code

    chat_id = 67890
    player1_id = 2001
    player2_id = 2002
    username1 = "group1"
    username2 = "group2"

    # Setup mock context
    context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
    context.args = []

    # Player 1 joins Group vs. AI
    update1 = MagicMock()
    update1.effective_chat.id = chat_id
    update1.effective_user.id = player1_id
    update1.effective_user.username = username1
    update1.message = AsyncMock()
    await join_group_ai(update1, context)
    update1.message.reply_text.assert_called_with(f"Player {player1_id} joined! Current players: 1. Use /start_group_ai when ready.")

    # Player 2 joins Group vs. AI
    update2 = MagicMock()
    update2.effective_chat.id = chat_id
    update2.effective_user.id = player2_id
    update2.effective_user.username = username2
    update2.message = AsyncMock()
    await join_group_ai(update2, context)
    update2.message.reply_text.assert_called_with(f"Player {player2_id} joined! Current players: 2. Use /start_group_ai when ready.")

    # Not enough players error (simulate with only 1 player)
    context.args = []
    update3 = MagicMock()
    update3.effective_chat.id = chat_id
    update3.effective_user.id = 9999
    update3.effective_user.username = "latecomer"
    update3.message = AsyncMock()
    # Try to start with only 1 player (should fail)
    pulse_code_group_ai_manager.end_game(chat_id)
    pulse_code_group_ai_manager.new_game(chat_id)
    await start_group_ai(update3, context)
    update3.message.reply_text.assert_called_with("Not enough players to start. At least 2 required.")

    # Start the game with 2 players
    pulse_code_group_ai_manager.end_game(chat_id)
    game = pulse_code_group_ai_manager.new_game(chat_id)
    game.add_player(player1_id)
    game.add_player(player2_id)
    context.args = []
    update1.message = AsyncMock()
    await start_group_ai(update1, context)
    update1.message.reply_text.assert_called()
    # Simulate AI selection callback (directly set AI and code for test)
    ai_code = "1234"
    game.set_ai("calculon", ai_code)
    game.active = True

    # Player 1 makes a wrong guess (valid turn)
    context.args = ["5678"]
    update1.message = AsyncMock()
    await group_guess(update1, context)
    print("CALLS after group player 1 guess:", update1.message.reply_text.call_args_list)
    update1.message.reply_text.assert_any_call("Guesser: 2001\nGuess: `5678`\nHits: 0 | Flashes: 0 | Static: 4\nYour Stress: 40%\nNext turn: Player 2002")

    # Player 1 tries to guess again (not their turn)
    context.args = ["4321"]
    update1.message = AsyncMock()
    await group_guess(update1, context)
    update1.message.reply_text.assert_called_with("It's not your turn.")

    # Player 2 makes a wrong guess
    context.args = ["5671"]
    update2.message = AsyncMock()
    await group_guess(update2, context)
    print("CALLS after group player 2 guess:", update2.message.reply_text.call_args_list)
    update2.message.reply_text.assert_any_call("Guesser: 2002\nGuess: `5671`\nHits: 0 | Flashes: 1 | Static: 3\nYour Stress: 30%\nNext turn: Player 2001")

    # Player 2 tries invalid guess (but it's not their turn)
    context.args = ["1111"]
    update2.message = AsyncMock()
    await group_guess(update2, context)
    update2.message.reply_text.assert_called_with("It's not your turn.")

    # Player 1 makes the winning guess
    context.args = ["1234"]
    update1.message = AsyncMock()
    await group_guess(update1, context)
    print("CALLS after group player 1 winning guess:", update1.message.reply_text.call_args_list)
    update1.message.reply_text.assert_any_call("Guesser: 2001\nGuess: `1234`\nHits: 4 | Flashes: 0 | Static: 0\nYour Stress: 40%\n\n🎉 Congratulations, Player 2001! You've cracked the code!")

    # Game should be ended
    assert pulse_code_group_ai_manager.get_game(chat_id) is None

    # Try status after game ended
    update1.message = AsyncMock()
    await group_status(update1, context)
    update1.message.reply_text.assert_called_with("You are not a player in this game.")

    # Try ending a non-existent game
    update1.message = AsyncMock()
    await end_group_ai(update1, context)
    update1.message.reply_text.assert_called_with("No active Group vs. AI game to end.")

@pytest.mark.asyncio
async def test_group_vs_group_full_flow():
    from bot.handlers.pulse_code_handlers import join_team_a, join_team_b, set_team_code, start_group_pvp, team_guess, team_status, end_group_pvp
    from bot.pulse_code_manager import pulse_code_group_pvp_manager
    from telegram.ext import ContextTypes
    from unittest.mock import MagicMock, AsyncMock

    chat_id = 78901
    a1_id = 3001
    a2_id = 3002
    b1_id = 4001
    b2_id = 4002

    # Setup mock context
    context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
    context.args = []

    # Team A player 1 joins
    update_a1 = MagicMock()
    update_a1.effective_chat.id = chat_id
    update_a1.effective_user.id = a1_id
    update_a1.message = AsyncMock()
    await join_team_a(update_a1, context)
    update_a1.message.reply_text.assert_called_with(f"Player {a1_id} joined Team A! Use /set_team_code <code> if you are the code setter. Use /start_group_pvp when both teams are ready.")

    # Team A player 2 joins
    update_a2 = MagicMock()
    update_a2.effective_chat.id = chat_id
    update_a2.effective_user.id = a2_id
    update_a2.message = AsyncMock()
    await join_team_a(update_a2, context)
    update_a2.message.reply_text.assert_called_with(f"Player {a2_id} joined Team A! Use /set_team_code <code> if you are the code setter. Use /start_group_pvp when both teams are ready.")

    # Team B player 1 joins
    update_b1 = MagicMock()
    update_b1.effective_chat.id = chat_id
    update_b1.effective_user.id = b1_id
    update_b1.message = AsyncMock()
    await join_team_b(update_b1, context)
    update_b1.message.reply_text.assert_called_with(f"Player {b1_id} joined Team B! Use /set_team_code <code> if you are the code setter. Use /start_group_pvp when both teams are ready.")

    # Team B player 2 joins
    update_b2 = MagicMock()
    update_b2.effective_chat.id = chat_id
    update_b2.effective_user.id = b2_id
    update_b2.message = AsyncMock()
    await join_team_b(update_b2, context)
    update_b2.message.reply_text.assert_called_with(f"Player {b2_id} joined Team B! Use /set_team_code <code> if you are the code setter. Use /start_group_pvp when both teams are ready.")

    # Team A sets code
    context.args = ["1234"]
    update_a1.message = AsyncMock()
    await set_team_code(update_a1, context)
    update_a1.message.reply_text.assert_any_call("Team A code set! Waiting for the other team.")

    # Team B sets code
    context.args = ["5678"]
    update_b1.message = AsyncMock()
    await set_team_code(update_b1, context)
    update_b1.message.reply_text.assert_any_call("Team B code set! Waiting for the other team.")
    update_b1.message.reply_text.assert_any_call("Both codes set! Team A goes first. Use /team_guess <4-unique-digits> to guess.")

    # Start the game
    context.args = []
    update_a1.message = AsyncMock()
    await start_group_pvp(update_a1, context)
    update_a1.message.reply_text.assert_called_with("Group vs. Group started! Team A goes first. Use /team_guess <4-unique-digits> to guess.")

    # Team A makes a wrong guess
    context.args = ["8765"]
    update_a1.message = AsyncMock()
    await team_guess(update_a1, context)
    print("CALLS after group pvp team A guess:", update_a1.message.reply_text.call_args_list)
    update_a1.message.reply_text.assert_any_call("Team: A\nGuesser: 3001\nGuess: `8765`\nHits: 0 | Flashes: 4 | Static: 0\nYour Stress: 0%\nNext turn: Team B")

    # Team A tries to guess again (not their turn)
    context.args = ["4321"]
    update_a1.message = AsyncMock()
    await team_guess(update_a1, context)
    update_a1.message.reply_text.assert_called_with("It's not your team's turn.")

    # Team B makes a wrong guess
    context.args = ["4321"]
    update_b1.message = AsyncMock()
    await team_guess(update_b1, context)
    update_b1.message.reply_text.assert_any_call("Team: B\nGuesser: 4001\nGuess: `4321`\nHits: 0 | Flashes: 4 | Static: 0\nYour Stress: 0%\nNext turn: Team A")

    # Team B tries invalid guess
    context.args = ["1111"]
    update_b1.message = AsyncMock()
    await team_guess(update_b1, context)
    update_b1.message.reply_text.assert_called_with("It's not your team's turn.")

    # Team A makes the winning guess
    context.args = ["5678"]
    update_a2.message = AsyncMock()
    await team_guess(update_a2, context)
    update_a2.message.reply_text.assert_any_call("Team: A\nGuesser: 3002\nGuess: `5678`\nHits: 4 | Flashes: 0 | Static: 0\nYour Stress: 0%\n\n🎉 Congratulations, Team A! You've cracked the code!")

    # Game should be ended
    assert pulse_code_group_pvp_manager.get_game(chat_id) is None

    # Try status after game ended
    update_a1.message = AsyncMock()
    await team_status(update_a1, context)
    update_a1.message.reply_text.assert_called_with("No active Group vs. Group game.")

    # Try ending a non-existent game
    update_a1.message = AsyncMock()
    await end_group_pvp(update_a1, context)
    update_a1.message.reply_text.assert_called_with("No active Group vs. Group game to end.")
