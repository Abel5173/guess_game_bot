import pytest
import asyncio
from bot.imposter_royale.game import ImposterRoyaleGame
from bot.imposter_royale.player import Player
from bot.database import init_db, SessionLocal
from bot.database.models import GameSession, PlayerGameLink, Player as PlayerModel

@pytest.fixture(scope="module", autouse=True)
def setup_db():
    init_db()
    yield
    db = SessionLocal()
    db.query(PlayerGameLink).delete()
    db.query(GameSession).delete()
    db.query(PlayerModel).delete()
    db.commit()
    db.close()

@pytest.fixture
def game():
    g = ImposterRoyaleGame(chat_id=123)
    loop = asyncio.get_event_loop()
    loop.run_until_complete(g.initialize())
    return g

@pytest.mark.asyncio
async def test_add_player(game):
    player = Player(1, "Test Player")
    await game.state.add_player(player)
    players = await game.state.get_all_players()
    assert len(players) == 1
    assert players[0].name == "Test Player"

@pytest.mark.asyncio
async def test_game_phase(game):
    await game.state.set_phase("test_phase")
    phase = await game.state.get_phase()
    assert phase == "test_phase"
