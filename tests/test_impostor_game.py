import pytest
from bot.impostor_game import ImpostorGame

def test_add_player():
    game = ImpostorGame()
    assert game.add_player(1, 'Alice')
    assert game.add_player(2, 'Bob')
    assert game.add_player(3, 'Charlie')
    assert game.add_player(4, 'Dana')
    assert not game.add_player(1, 'Alice')  # Already joined

def test_start_game_and_roles():
    game = ImpostorGame()
    for i, name in enumerate(['A', 'B', 'C', 'D'], 1):
        game.add_player(i, name)
    assert game.start_game()
    roles = [p['role'] for p in game.players.values()]
    assert roles.count('impostor') == 1
    assert roles.count('crewmate') == 3

def test_vote_and_resolve():
    game = ImpostorGame()
    for i, name in enumerate(['A', 'B', 'C', 'D'], 1):
        game.add_player(i, name)
    game.start_game()
    alive = list(game.get_alive_players().keys())
    voter, target = alive[0], alive[1]
    game.vote(voter, target)
    voted_out, msg = game.resolve_votes()
    assert voted_out == target or voted_out is None
    assert isinstance(msg, str)

def test_game_over():
    game = ImpostorGame()
    for i, name in enumerate(['A', 'B', 'C', 'D'], 1):
        game.add_player(i, name)
    game.start_game()
    # Kill impostor
    impostor_id = [uid for uid, p in game.players.items() if p['role'] == 'impostor'][0]
    game.players[impostor_id]['alive'] = False
    over, msg = game.check_game_over()
    assert over
    assert "win" in msg.lower() 