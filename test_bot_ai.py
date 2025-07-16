#!/usr/bin/env python3
"""
Test script to verify the bot's AI functions work with the new Chat Completion API.
"""

import asyncio
import sys
import os
import pytest

# Add the bot directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "bot"))

from bot.utils import query_ai, generate_clue, generate_complex_clue
from bot.tasks.clue_tasks import ai_riddle_task, get_random_task


@pytest.mark.asyncio
async def test_bot_ai_functions():
    """Test all the bot's AI functions."""
    print("🤖 Testing Bot AI Functions with Chat Completion API")
    print("=" * 60)

    # Test 1: Basic AI query
    print("\n1️⃣ Testing Basic AI Query")
    try:
        result = await query_ai("Hello! How are you today?")
        print("✅ Basic AI query successful!")
        print(f"🤖 Response: {result}")
    except Exception as e:
        print(f"❌ Basic AI query failed: {e}")

    # Test 2: Generate clue
    print("\n2️⃣ Testing Clue Generation")
    try:
        result = await generate_clue(["Alice", "Bob", "Charlie"])
        print("✅ Clue generation successful!")
        print(f"🤖 Clue: {result}")
    except Exception as e:
        print(f"❌ Clue generation failed: {e}")

    # Test 3: Generate complex clue with history
    print("\n3️⃣ Testing Complex Clue Generation")
    try:
        result = await generate_complex_clue(
            ["Alice", "Bob", "Charlie"],
            "Alice said she was working on the task, Bob was quiet, Charlie asked many questions.",
        )
        print("✅ Complex clue generation successful!")
        print(f"🤖 Complex Clue: {result}")
    except Exception as e:
        print(f"❌ Complex clue generation failed: {e}")

    # Test 4: AI riddle task
    print("\n4️⃣ Testing AI Riddle Task")
    try:
        task_type, riddle, answer = await ai_riddle_task(["Alice", "Bob", "Charlie"])
        print("✅ AI riddle task successful!")
        print(f"🤖 Task Type: {task_type}")
        print(f"🤖 Riddle: {riddle}")
        print(f"🤖 Answer: {answer}")
    except Exception as e:
        print(f"❌ AI riddle task failed: {e}")

    # Test 5: Random task
    print("\n5️⃣ Testing Random Task")
    try:
        task_type, task, answer = await get_random_task(["Alice", "Bob", "Charlie"])
        print("✅ Random task successful!")
        print(f"🤖 Task Type: {task_type}")
        print(f"🤖 Task: {task}")
        print(f"🤖 Answer: {answer}")
    except Exception as e:
        print(f"❌ Random task failed: {e}")


def main():
    """Main test function."""
    print("🎮 Bot AI Functionality Test")
    print("=" * 60)

    # Run the async tests
    asyncio.run(test_bot_ai_functions())

    print("\n✅ All tests completed!")


if __name__ == "__main__":
    main()
