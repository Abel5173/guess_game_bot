import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from types import SimpleNamespace
from bot.impostor import ImpostorGame
from bot.database import init_db, SessionLocal
from bot.database.models import Player, Task
from bot.ui.buttons import main_menu, voting_menu, join_game_menu, confirm_end_game
from bot.impostor.utils import calculate_title
from bot.tasks import clue_tasks

@pytest.fixture
def setup_db():
    """Initialize database for each test"""
    init_db()
    yield
    # Cleanup after test

@pytest.fixture
def game():
    """Create a fresh game instance"""
    return ImpostorGame()

@pytest.fixture
def context():
    """Create a mock context"""
    return AsyncMock()

@pytest.fixture
def users():
    """Create test users"""
    return [
        SimpleNamespace(id=1, first_name='Alice'),
        SimpleNamespace(id=2, first_name='Bob'),
        SimpleNamespace(id=3, first_name='Charlie'),
        SimpleNamespace(id=4, first_name='Dana'),
        SimpleNamespace(id=5, first_name='Eve'),
        SimpleNamespace(id=6, first_name='Frank'),
    ]

@pytest.fixture
def update_template():
    """Create a template for update objects"""
    def create_update(user, callback_data=None):
        update = MagicMock()
        update.effective_user = user
        update.effective_chat = SimpleNamespace(id=12345)
        update.callback_query = MagicMock()
        update.callback_query.from_user = user
        update.callback_query.message = MagicMock()
        update.callback_query.message.reply_text = AsyncMock()
        update.callback_query.message.edit_reply_markup = AsyncMock()
        update.callback_query.answer = AsyncMock()
        update.message = MagicMock()
        update.message.reply_text = AsyncMock()
        if callback_data:
            update.callback_query.data = callback_data
        return update
    return create_update

# ============================================================================
# CORE GAME LOGIC TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_game_initialization(game):
    """Test game initialization with default and custom config"""
    # Test default config
    assert game.core.config['min_players'] == 4
    assert game.core.config['impostor_count'] == 1
    assert game.core.phase == 'waiting'
    assert not game.core.started
    assert len(game.core.players) == 0
    assert len(game.core.impostors) == 0

    # Test custom config
    custom_game = ImpostorGame({
        'min_players': 6,
        'impostor_count': 2,
        'tasks_required': 5
    })
    assert custom_game.core.config['min_players'] == 6
    assert custom_game.core.config['impostor_count'] == 2

@pytest.mark.asyncio
async def test_player_management(game, users):
    """Test all player management scenarios"""
    # Test adding players
    for user in users[:4]:
        assert game.add_player(user.id, user.first_name)
        assert user.id in game.core.players
        assert game.core.players[user.id]['name'] == user.first_name
        assert game.core.players[user.id]['alive'] == True

    # Test double join prevention
    assert not game.add_player(users[0].id, users[0].first_name)

    # Test game start prevents new joins
    game.core.start_game()
    assert not game.add_player(users[4].id, users[4].first_name)

@pytest.mark.asyncio
async def test_game_start_conditions(game, users):
    """Test all game start conditions and scenarios"""
    # Test insufficient players
    for user in users[:3]:  # Only 3 players
        game.add_player(user.id, user.first_name)
    assert not game.core.start_game()
    assert not game.core.started

    # Test sufficient players
    game.add_player(users[3].id, users[3].first_name)  # Now 4 players
    assert game.core.start_game()
    assert game.core.started
    assert game.core.phase == 'task'
    assert len(game.core.impostors) == 1

    # Test impostor assignment
    impostor_id = list(game.core.impostors)[0]
    assert impostor_id in game.core.players
    assert game.core.players[impostor_id]['alive'] == True

@pytest.mark.asyncio
async def test_role_assignment(game, users):
    """Test role assignment logic"""
    for user in users[:4]:
        game.add_player(user.id, user.first_name)
    
    game.core.assign_roles()
    assert len(game.core.impostors) == 1
    impostor_id = list(game.core.impostors)[0]
    assert impostor_id in game.core.players

    # Test multiple impostors
    game2 = ImpostorGame({'impostor_count': 2})
    for user in users[:4]:
        game2.add_player(user.id, user.first_name)
    game2.core.assign_roles()
    assert len(game2.core.impostors) == 2

@pytest.mark.asyncio
async def test_game_over_conditions(game, users):
    """Test all game over conditions"""
    for user in users[:4]:
        game.add_player(user.id, user.first_name)
    game.core.start_game()

    # Test crewmate win (all impostors eliminated)
    game.core.impostors.clear()
    over, msg = game.core.check_game_over()
    assert over
    assert 'win' in msg

    # Test impostor win (impostors > crewmates)
    # Reset by adding impostors back and killing crewmates
    game.core.impostors = {1}  # Set player 1 as impostor
    # Ensure the impostor is alive
    game.core.players[1]['alive'] = True
    crewmate_ids = [uid for uid in game.core.players if uid not in game.core.impostors]
    # Kill all crewmates to make impostors outnumber them
    for uid in crewmate_ids:
        game.core.players[uid]['alive'] = False
    over, msg = game.core.check_game_over()
    assert over
    assert 'win' in msg

    # Test game continues
    game.core.players[crewmate_ids[0]]['alive'] = True
    game.core.players[1]['alive'] = True
    over, msg = game.core.check_game_over()
    assert not over
    assert msg == ""

@pytest.mark.asyncio
async def test_game_reset_functionality(game, users, update_template):
    """Test game reset functionality"""
    # Setup a game in progress
    for user in users[:4]:
        game.add_player(user.id, user.first_name)
    game.core.start_game()
    game.core.phase = 'voting'
    game.core.votes = {1: 2}
    
    # Test reset
    update = update_template(users[0])
    await game.reset(update)
    
    # Verify reset state
    assert len(game.core.players) == 0
    assert len(game.core.impostors) == 0
    assert not game.core.started
    assert game.core.phase == 'waiting'
    assert len(game.core.votes) == 0

# ============================================================================
# PHASE MANAGEMENT TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_phase_transitions(game, users, context):
    """Test all phase transitions"""
    # Setup game
    for user in users[:4]:
        game.add_player(user.id, user.first_name)
    game.core.start_game()
    
    # Test task phase
    assert game.core.phase == 'task'
    
    # Test discussion phase
    await game.phases.start_discussion_phase(context)
    assert game.core.phase == 'discussion'
    assert len(game.core.discussion_history) == 0
    
    # Test voting phase
    await game.phases.start_voting_phase(context)
    assert game.core.phase == 'voting'
    assert len(game.core.votes) == 0

@pytest.mark.asyncio
async def test_discussion_history(game, users, update_template):
    """Test discussion history tracking"""
    for user in users[:4]:
        game.add_player(user.id, user.first_name)
    game.core.start_game()
    game.core.phase = 'discussion'
    
    # Simulate discussion messages
    messages = [
        "I think Bob is suspicious",
        "No way, Alice is the impostor!",
        "Let's vote for Charlie"
    ]
    
    for i, message in enumerate(messages):
        update = update_template(users[i])
        update.message.text = message
        await game.handle_discussion(update, AsyncMock())
    
    assert len(game.core.discussion_history) == 3
    assert "Alice: I think Bob is suspicious" in game.core.discussion_history[0]
    assert "Bob: No way, Alice is the impostor!" in game.core.discussion_history[1]

# ============================================================================
# CONFIGURATION TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_custom_configurations():
    """Test various game configurations"""
    configs = [
        {'min_players': 3, 'impostor_count': 1},
        {'min_players': 6, 'impostor_count': 2},
        {'min_players': 8, 'impostor_count': 3},
        {'min_players': 4, 'impostor_count': 1, 'tasks_required': 5},
        {'min_players': 4, 'impostor_count': 1, 'anonymous_voting': False},
    ]
    
    for config in configs:
        game = ImpostorGame(config)
        assert game.core.config['min_players'] == config['min_players']
        assert game.core.config['impostor_count'] == config['impostor_count']
        
        if 'tasks_required' in config:
            assert game.core.config['tasks_required'] == config['tasks_required']
        
        if 'anonymous_voting' in config:
            assert game.core.config['anonymous_voting'] == config['anonymous_voting']

# ============================================================================
# ERROR HANDLING AND EDGE CASES
# ============================================================================

@pytest.mark.asyncio
async def test_error_conditions(game, users, update_template):
    """Test error handling and edge cases"""
    # Test actions when not enough players
    update = update_template(users[0], "start_voting")
    await game.handle_start_voting(update, AsyncMock())
    
    # Test actions when game not started
    update = update_template(users[0], "complete_task")
    await game.handle_complete_task(update, AsyncMock())
    
    # Test invalid callback data
    update = update_template(users[0], "invalid_callback")
    # Should not raise exception
    
    # Test database connection errors
    with patch('bot.database.SessionLocal') as mock_session:
        mock_session.side_effect = Exception("Database error")
        update = update_template(users[0], "show_profile")
        await game.show_profile(update)

@pytest.mark.asyncio
async def test_concurrent_operations(game, users, update_template):
    """Test concurrent operations and race conditions"""
    # Test multiple players joining simultaneously
    updates = [update_template(user, "join_game") for user in users[:4]]
    
    # Simulate concurrent joins
    for update in updates:
        await game.handle_join_game(update, AsyncMock())
    
    assert len(game.core.players) == 4
    
    # Test multiple task completions
    updates = [update_template(user, "complete_task") for user in users[:4]]
    for update in updates:
        await game.handle_complete_task(update, AsyncMock())

# ============================================================================
# PERFORMANCE AND STRESS TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_large_game_session(setup_db, game, update_template):
    """Test game with many players"""
    # Create many players
    many_users = [SimpleNamespace(id=i, first_name=f'Player{i}') for i in range(1, 21)]
    
    # Add all players
    for user in many_users:
        update = update_template(user, "join_game")
        await game.handle_join_game(update, AsyncMock())
    
    assert len(game.core.players) == 20
    
    # Start game
    update = update_template(many_users[0], "start_impostor")
    await game.start_impostor_game(update, AsyncMock())
    
    # Complete tasks for all
    for user in many_users:
        update = update_template(user, "complete_task")
        await game.handle_complete_task(update, AsyncMock())
    
    # Test voting with many players
    update = update_template(many_users[0], "start_voting")
    await game.handle_start_voting(update, AsyncMock())

@pytest.mark.asyncio
async def test_rapid_operations(setup_db, game, users, update_template):
    """Test rapid operations to ensure stability"""
    # Rapid joins
    for user in users:
        update = update_template(user, "join_game")
        await game.handle_join_game(update, AsyncMock())
    
    # Rapid task completions
    for user in users:
        update = update_template(user, "complete_task")
        await game.handle_complete_task(update, AsyncMock())
    
    # Rapid button presses
    buttons = ["show_profile", "show_leaderboard", "show_rules"]
    for button in buttons:
        for user in users[:3]:
            update = update_template(user, button)
            if button == "show_profile":
                await game.show_profile(update)
            elif button == "show_leaderboard":
                await game.show_leaderboard(update)
            elif button == "show_rules":
                await game.show_rules(update)

# ============================================================================
# SECURITY AND VALIDATION TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_input_validation(game, update_template):
    """Test input validation and security"""
    # Test invalid user IDs
    invalid_user = SimpleNamespace(id=-1, first_name='Invalid')
    update = update_template(invalid_user, "join_game")
    await game.handle_join_game(update, AsyncMock())
    
    # Test very long names
    long_name_user = SimpleNamespace(id=999, first_name='A' * 1000)
    update = update_template(long_name_user, "join_game")
    await game.handle_join_game(update, AsyncMock())
    
    # Test special characters in names
    special_user = SimpleNamespace(id=998, first_name='Test<script>alert("xss")</script>')
    update = update_template(special_user, "join_game")
    await game.handle_join_game(update, AsyncMock())

# ============================================================================
# MEMORY AND RESOURCE TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_memory_cleanup(game, users, update_template):
    """Test memory cleanup and resource management"""
    # Create many games
    games = []
    for i in range(10):
        g = ImpostorGame()
        for user in users[:4]:
            g.add_player(user.id, user.first_name)
        games.append(g)
    
    # Reset all games
    for g in games:
        update = update_template(users[0])
        await g.reset(update)
    
    # Verify cleanup
    for g in games:
        assert len(g.core.players) == 0
        assert len(g.core.impostors) == 0
        assert not g.core.started

@pytest.mark.asyncio
async def test_database_connection_management(setup_db, game, users, update_template):
    """Test database connection management"""
    db = SessionLocal()
    db.query(Player).delete()
    db.commit()
    db.close()
    for user in users:
        update = update_template(user, "join_game")
        await game.handle_join_game(update, AsyncMock())
    db = SessionLocal()
    players = db.query(Player).all()
    assert len(players) == len(users)
    db.close()
    update = update_template(users[0], "show_profile")
    await game.show_profile(update) 