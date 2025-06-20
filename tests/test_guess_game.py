import pytest
from bot.guess_game import GuessGame

def test_add_player():
    game = GuessGame()
    assert game.add_player(1, 'Alice')
    assert game.add_player(2, 'Bob')
    assert not game.add_player(3, 'Charlie')  # Only 2 players allowed

def test_set_secret_and_ready():
    game = GuessGame()
    game.add_player(1, 'Alice')
    game.set_secret(1, '1234')
    assert game.players[1]['secret'] == '1234'
    assert game.players[1]['ready']

def test_score_guess():
    game = GuessGame()
    N, O = game.score_guess('1234', '1243')
    assert N == 4  # All digits present
    assert O == 2  # 1 and 2 in correct place

def test_reset():
    game = GuessGame()
    game.add_player(1, 'Alice')
    game.set_secret(1, '1234')
    game.reset()
    assert game.players == {}
    assert game.group_chat_id is None
    assert not game.started 