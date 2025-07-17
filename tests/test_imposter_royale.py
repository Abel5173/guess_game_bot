import pytest
from bot.imposter_royale.game import ImposterRoyaleGame
from bot.imposter_royale.player import Player

@pytest.fixture
def game():
    return ImposterRoyaleGame(chat_id=123)

def test_add_player(game):
    game.state.r.flushdb()
    player = Player(1, "Test Player")
    game.state.add_player(player)
    players = game.state.get_all_players()
    assert len(players) == 1
    assert players[0]['name'] == "Test Player"

def test_game_phase(game):
    game.state.r.flushdb()
    game.state.set_phase("test_phase")
    phase = game.state.get_phase()
    assert phase == "test_phase"
