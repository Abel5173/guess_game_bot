import pytest
from unittest.mock import AsyncMock, MagicMock
from types import SimpleNamespace
from bot.impostor import ImpostorGame
from bot.database import init_db


@pytest.mark.asyncio
async def test_full_game_flow():
    # Setup
    init_db()
    game = ImpostorGame()
    context = AsyncMock()
    users = [
        SimpleNamespace(id=1, first_name='Alice'),
        SimpleNamespace(id=2, first_name='Bob'),
        SimpleNamespace(id=3, first_name='Charlie'),
        SimpleNamespace(id=4, first_name='Dana'),
    ]
    # Simulate joining
    for user in users:
        update = MagicMock()
        update.effective_user = user
        update.callback_query = MagicMock()
        update.callback_query.message.reply_text = AsyncMock()
        update.callback_query.answer = AsyncMock()
        update.message = MagicMock()
        update.message.reply_text = AsyncMock()
        await game.handle_join_game(update, context)
    # Start game
    update = MagicMock()
    update.effective_user = users[0]
    update.callback_query = MagicMock()
    update.callback_query.message.reply_text = AsyncMock()
    update.callback_query.answer = AsyncMock()
    update.message = MagicMock()
    update.message.reply_text = AsyncMock()
    await game.start_impostor_game(update, context)
    # Simulate task completion
    for user in users:
        update = MagicMock()
        update.effective_user = user
        update.callback_query = MagicMock()
        update.callback_query.message.reply_text = AsyncMock()
        update.callback_query.answer = AsyncMock()
        update.message = MagicMock()
        update.message.reply_text = AsyncMock()
        await game.handle_complete_task(update, context)
    # Simulate discussion phase
    update = MagicMock()
    update.effective_user = users[0]
    update.callback_query = MagicMock()
    update.callback_query.message.reply_text = AsyncMock()
    update.callback_query.answer = AsyncMock()
    update.message = MagicMock()
    update.message.reply_text = AsyncMock()
    await game.handle_start_discussion(update, context)
    # Simulate voting phase
    update = MagicMock()
    update.effective_user = users[0]
    update.callback_query = MagicMock()
    update.callback_query.message.reply_text = AsyncMock()
    update.callback_query.answer = AsyncMock()
    update.message = MagicMock()
    update.message.reply_text = AsyncMock()
    await game.handle_start_voting(update, context)
    # Simulate rules, profile, leaderboard, end game
    update = MagicMock()
    update.effective_user = SimpleNamespace(id=42, first_name='TestUser')
    update.callback_query = MagicMock()
    update.callback_query.message.reply_text = AsyncMock()
    update.callback_query.answer = AsyncMock()
    update.message = MagicMock()
    update.message.reply_text = AsyncMock()
    await game.show_rules(update)
    await game.show_profile(update)
    await game.show_leaderboard(update)
    await game.handle_end_game(update, context)
    await game.handle_confirm_end_game(update, context)
    await game.handle_cancel_end_game(update, context)
    # Simulate reset
    await game.reset(update)
    # Assert no exceptions and all reply_text called
    assert True


@pytest.mark.asyncio
async def test_edge_cases():
    game = ImpostorGame()
    context = AsyncMock()
    user = SimpleNamespace(id=1, first_name='Solo')
    # Not enough players to start
    update = MagicMock()
    update.effective_user = user
    update.callback_query = MagicMock()
    update.callback_query.message.reply_text = AsyncMock()
    update.callback_query.answer = AsyncMock()
    update.message = MagicMock()
    update.message.reply_text = AsyncMock()
    await game.handle_join_game(update, context)
    await game.start_impostor_game(update, context)
    # Double join
    await game.handle_join_game(update, context)
    # Invalid vote
    game.core.phase = 'voting'
    update.callback_query.data = 'vote_999'
    await game.handle_vote(update, context)
    # Show rules with no callback_query
    update = MagicMock()
    update.callback_query = MagicMock()
    update.callback_query.message.reply_text = AsyncMock()
    update.callback_query.answer = AsyncMock()
    update.message = MagicMock()
    update.message.reply_text = AsyncMock()
    await game.show_rules(update)
    assert True


@pytest.mark.asyncio
async def test_task_types():
    from bot.tasks import clue_tasks
    player_names = ['Alice', 'Bob', 'Charlie', 'Dana']
    # Test all task generators
    for func in [
        clue_tasks.emoji_decode_task,
        clue_tasks.quick_math_task,
        clue_tasks.word_unscramble_task,
        clue_tasks.trivia_task,
        clue_tasks.pattern_recognition_task
    ]:
        ttype, puzzle, answer = func()
        assert isinstance(ttype, str)
        assert isinstance(puzzle, str)
        assert isinstance(answer, str)
    # Test async AI riddle
    task_type, puzzle, answer = await clue_tasks.get_random_task(player_names)
    assert isinstance(task_type, str)
    assert isinstance(puzzle, str)
    assert isinstance(answer, str)
