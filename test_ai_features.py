#!/usr/bin/env python3
"""
Test AI Features - Comprehensive test for all AI-powered game features.
"""

import asyncio
import sys
import os
from datetime import datetime
import pytest

# Add the bot directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'bot'))

from bot.ai import ai_game_engine
from bot.ai.llm_client import ai_client
from bot.ai.game_master import ai_game_master
from bot.ai.task_generator import ai_task_generator
from bot.ai.voting_analyzer import ai_voting_analyzer
from bot.ai.chaos_events import ai_chaos_events


@pytest.mark.asyncio
async def test_llm_client():
    """Test the LLM client functionality."""
    print("🧪 Testing LLM Client...")
    
    try:
        # Test basic text generation
        response = await ai_client.generate_text("Hello, this is a test.")
        print(f"✅ Text generation: {response[:100]}...")
        
        # Test narrative generation
        narrative = await ai_client.generate_narrative("space station", "crewmate", "Abel")
        print(f"✅ Narrative generation: {narrative[:100]}...")
        
        # Test task generation
        task = await ai_client.generate_task("crewmate", "engineering bay")
        print(f"✅ Task generation: {task[:100]}...")
        
        return True
    except Exception as e:
        print(f"❌ LLM Client test failed: {e}")
        return False


@pytest.mark.asyncio
async def test_game_master():
    """Test the AI Game Master functionality."""
    print("\n🎭 Testing AI Game Master...")
    
    try:
        # Test game initialization
        intro = await ai_game_master.initialize_game(1, 5)
        print(f"✅ Game initialization: {intro[:100]}...")
        
        # Test persona assignment
        player_ids = [123, 456, 789]
        personas = await ai_game_master.assign_player_personas(1, player_ids)
        print(f"✅ Persona assignment: {len(personas)} personas created")
        
        # Test game conclusion
        game_result = {"winner": "crewmates", "rounds": 3}
        conclusion = await ai_game_master.conclude_game(1, game_result)
        print(f"✅ Game conclusion: {conclusion[:100]}...")
        
        # Test world lore
        lore = await ai_game_master.generate_world_lore()
        print(f"✅ World lore: {lore[:100]}...")
        
        return True
    except Exception as e:
        print(f"❌ Game Master test failed: {e}")
        return False


@pytest.mark.asyncio
async def test_task_generator():
    """Test the AI Task Generator functionality."""
    print("\n🎯 Testing AI Task Generator...")
    
    try:
        # Test task generation
        task_data = await ai_task_generator.generate_task(1, 123, "crewmate")
        print(f"✅ Task generation: {task_data['description'][:100]}...")
        
        # Test impostor task
        impostor_task = await ai_task_generator.generate_task(1, 456, "impostor")
        print(f"✅ Impostor task: {impostor_task['description'][:100]}...")
        
        # Test task progress
        progress = ai_task_generator.get_task_progress(1, 123)
        print(f"✅ Task progress: {progress}")
        
        return True
    except Exception as e:
        print(f"❌ Task Generator test failed: {e}")
        return False


@pytest.mark.asyncio
async def test_voting_analyzer():
    """Test the AI Voting Analyzer functionality."""
    print("\n🕵️ Testing AI Voting Analyzer...")
    
    try:
        # Test voting analysis
        vote_results = {
            "Abel": 3,
            "Bob": 1,
            "Charlie": 0
        }
        analysis = await ai_voting_analyzer.analyze_voting_round(1, vote_results, 1)
        print(f"✅ Voting analysis: {analysis[:100]}...")
        
        # Test behavior tracking
        ai_voting_analyzer.track_player_behavior(1, 123, "vote", {"target": "Abel", "time": 30})
        print("✅ Behavior tracking")
        
        # Test suspicion score
        score = ai_voting_analyzer.get_suspicion_score(1, 123)
        print(f"✅ Suspicion score: {score}")
        
        # Test leaderboard generation
        leaderboard = await ai_voting_analyzer.generate_suspicion_leaderboard(1)
        print(f"✅ Suspicion leaderboard: {leaderboard[:100]}...")
        
        return True
    except Exception as e:
        print(f"❌ Voting Analyzer test failed: {e}")
        return False


@pytest.mark.asyncio
async def test_chaos_events():
    """Test the AI Chaos Events functionality."""
    print("\n⚡ Testing AI Chaos Events...")
    
    try:
        # Test chaos event generation
        event = await ai_chaos_events.generate_chaos_event(1, "system_failure")
        print(f"✅ Chaos event generation: {event.name}")
        print(f"   Description: {event.description[:100]}...")
        
        # Test event activation
        event.activate()
        print(f"✅ Event activation: {event.active}")
        
        # Test event expiration
        expired = event.is_expired()
        print(f"✅ Event expiration check: {expired}")
        
        # Test chaos stats
        stats = ai_chaos_events.get_chaos_stats(1)
        print(f"✅ Chaos stats: {stats}")
        
        return True
    except Exception as e:
        print(f"❌ Chaos Events test failed: {e}")
        return False


@pytest.mark.asyncio
async def test_ai_game_engine():
    """Test the main AI Game Engine integration."""
    print("\n🤖 Testing AI Game Engine Integration...")
    
    try:
        # Test game initialization with AI
        intro = await ai_game_engine.initialize_game_with_ai(1, 5)
        print(f"✅ AI game initialization: {intro[:100]}...")
        
        # Test AI task generation
        task = await ai_game_engine.generate_ai_task(1, 123, "crewmate")
        print(f"✅ AI task: {task[:100]}...")
        
        # Test voting analysis
        vote_results = {"Abel": 2, "Bob": 1}
        analysis = await ai_game_engine.analyze_voting_with_ai(1, vote_results, 1)
        print(f"✅ AI voting analysis: {analysis[:100]}...")
        
        # Test chaos events
        events = await ai_game_engine.check_chaos_events(1)
        print(f"✅ Chaos events check: {len(events)} events")
        
        # Test AI stats
        stats = ai_game_engine.get_ai_stats(1)
        print(f"✅ AI stats: {stats}")
        
        # Test enabled features
        features = ai_game_engine.get_enabled_features()
        print(f"✅ Enabled features: {features}")
        
        return True
    except Exception as e:
        print(f"❌ AI Game Engine test failed: {e}")
        return False


@pytest.mark.asyncio
async def test_feature_toggles():
    """Test AI feature enable/disable functionality."""
    print("\n🔧 Testing AI Feature Toggles...")
    
    try:
        # Test disabling features
        ai_game_engine.disable_feature("ai_narrative")
        features = ai_game_engine.get_enabled_features()
        print(f"✅ Disabled ai_narrative: {'ai_narrative' not in features}")
        
        # Test enabling features
        ai_game_engine.enable_feature("ai_narrative")
        features = ai_game_engine.get_enabled_features()
        print(f"✅ Enabled ai_narrative: {'ai_narrative' in features}")
        
        return True
    except Exception as e:
        print(f"❌ Feature toggles test failed: {e}")
        return False


async def run_all_tests():
    """Run all AI feature tests."""
    print("🚀 Starting AI Features Test Suite")
    print("=" * 50)
    
    tests = [
        ("LLM Client", test_llm_client),
        ("Game Master", test_game_master),
        ("Task Generator", test_task_generator),
        ("Voting Analyzer", test_voting_analyzer),
        ("Chaos Events", test_chaos_events),
        ("AI Game Engine", test_ai_game_engine),
        ("Feature Toggles", test_feature_toggles)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            success = await test_func()
            results[test_name] = success
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
            results[test_name] = False
    
    # Print summary
    print("\n" + "=" * 50)
    print("📊 AI Features Test Results")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for test_name, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{test_name:20} {status}")
        if success:
            passed += 1
    
    print(f"\n🎯 Overall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All AI features are working correctly!")
        return True
    else:
        print("⚠️  Some AI features need attention.")
        return False


if __name__ == "__main__":
    print("🤖 AI-Powered Impostor Game - Feature Test Suite")
    print(f"⏰ Started at: {datetime.now()}")
    
    try:
        success = asyncio.run(run_all_tests())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n🛑 Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Test suite crashed: {e}")
        sys.exit(1) 