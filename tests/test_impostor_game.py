import pytest
from bot.impostor import ImpostorGame
from bot.utils import generate_complex_clue
from unittest.mock import AsyncMock, MagicMock


@pytest.mark.asyncio
async def test_discussion_phase():
    game = ImpostorGame()
    for i, name in enumerate(['A', 'B', 'C', 'D'], 1):
        game.add_player(i, name)
    game.core.start_game()
    context = AsyncMock()
    await game.phases.start_discussion_phase(context)
    assert game.core.phase == 'discussion'
    assert game.core.discussion_history == []
    context.bot.send_message.assert_called()


@pytest.mark.asyncio
async def test_voting_phase():
    game = ImpostorGame()
    for i, name in enumerate(['A', 'B', 'C', 'D'], 1):
        game.add_player(i, name)
    game.core.start_game()
    context = AsyncMock()
    await game.phases.start_voting_phase(context)
    assert game.core.phase == 'voting'
    assert game.core.votes == {}
    context.bot.send_message.assert_called()


@pytest.mark.asyncio
async def test_handle_vote():
    game = ImpostorGame()
    for i, name in enumerate(['A', 'B', 'C', 'D'], 1):
        game.add_player(i, name)
    game.core.start_game()
    game.core.phase = 'voting'
    update = MagicMock()
    update.callback_query = MagicMock()
    update.callback_query.from_user.id = 1
    update.callback_query.data = "vote_2"
    update.callback_query.answer = AsyncMock()
    update.callback_query.message.reply_text = AsyncMock()
    context = AsyncMock()
    await game.handle_vote(update, context)
    assert game.core.votes.get(1) == 2
    update.callback_query.answer.assert_called()
    update.callback_query.message.reply_text.assert_called()


@pytest.mark.asyncio
async def test_generate_complex_clue():
    clue = await generate_complex_clue(
        ['Alice', 'Bob', 'Charlie', 'Dana'],
        history="Alice: I suspect Bob!"
    )
    assert isinstance(clue, str)
