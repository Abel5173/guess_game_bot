import pytest
from typing import Any
from bot.impostor.core import ImpostorCore
from bot.impostor.utils import calculate_title


@pytest.fixture
def core() -> ImpostorCore:
    return ImpostorCore({"min_players": 4, "impostor_count": 1})


def test_add_player(core: ImpostorCore) -> None:
    assert core.add_player(1, "Alice")
    assert not core.add_player(1, "Alice")  # double join
    assert core.players[1]["name"] == "Alice"


def test_assign_roles(core: ImpostorCore) -> None:
    for i in range(1, 5):
        core.add_player(i, f"P{i}")
    core.assign_roles()
    assert len(core.impostors) == 1
    assert all(uid in core.players for uid in core.impostors)


def test_start_game(core: ImpostorCore) -> None:
    for i in range(1, 5):
        core.add_player(i, f"P{i}")
    assert core.start_game()
    assert core.started
    assert core.phase == "task"
    assert len(core.impostors) == 1


def test_start_game_not_enough(core: ImpostorCore) -> None:
    for i in range(1, 3):
        core.add_player(i, f"P{i}")
    assert not core.start_game()
    assert not core.started


def test_vote_and_resolve(core: ImpostorCore) -> None:
    for i in range(1, 5):
        core.add_player(i, f"P{i}")
    core.start_game()
    core.votes = {1: 2, 2: 2, 3: 4, 4: 2}
    voted_out, msg = core.resolve_votes()
    assert voted_out == 2
    assert "ejected" in msg
    assert not core.players[2]["alive"]


def test_vote_tie(core: ImpostorCore) -> None:
    for i in range(1, 5):
        core.add_player(i, f"P{i}")
    core.start_game()
    core.votes = {1: 2, 2: 3, 3: 2, 4: 3}
    voted_out, msg = core.resolve_votes()
    assert voted_out is None
    assert "tie" in msg


def test_check_game_over(core: ImpostorCore) -> None:
    for i in range(1, 5):
        core.add_player(i, f"P{i}")
    core.start_game()
    # Remove impostors to simulate crewmate win
    core.impostors.clear()
    over, msg, _ = core.check_game_over()
    assert over
    assert "win" in msg
    # Impostors > crewmates (kill crewmates so impostors outnumber them)
    core.impostors = set(list(core.players.keys())[:2])  # 2 impostors
    # Kill 2 crewmates so impostors outnumber crewmates (2 vs 0)
    for i in range(3, 5):
        core.players[i]["alive"] = False
    over, msg, _ = core.check_game_over()
    assert over
    assert "win" in msg


def test_reset(core: ImpostorCore) -> None:
    for i in range(1, 5):
        core.add_player(i, f"P{i}")
    core.start_game()
    core.reset()
    assert not core.players
    assert not core.impostors
    assert not core.started
    assert core.phase == "waiting"


def test_calculate_title() -> None:
    assert calculate_title(0) == "Rookie"
    assert calculate_title(30) == "Apprentice"
    assert calculate_title(60) == "Sleuth"
    assert calculate_title(120) == "Veteran"
    assert calculate_title(200) == "Mastermind"
    assert calculate_title(300) == "Legend"
