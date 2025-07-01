#!/usr/bin/env python3
"""
Test script to interact with Hugging Face API and test the AI functionality.
"""

import os
import asyncio
import requests
from dotenv import load_dotenv
import pytest

# Load environment variables
load_dotenv()
HF_API_KEY = os.getenv("HF_API_KEY")

def test_hf_connection():
    """Test basic connection to Hugging Face API."""
    print("🔍 Testing Hugging Face API Connection")
    print("=" * 50)
    
    if not HF_API_KEY:
        print("❌ HF_API_KEY not found in environment")
        return False, None
    
    print(f"✅ HF_API_KEY found: {HF_API_KEY[:10]}...")
    
    # Try different models
    models = [
        "microsoft/DialoGPT-medium",
        "microsoft/DialoGPT-small", 
        "microsoft/DialoGPT-large",
        "gpt2",
        "distilgpt2"
    ]
    
    headers = {"Authorization": f"Bearer {HF_API_KEY}"}
    test_prompt = "Hello, how are you?"
    
    for model in models:
        print(f"\n🔍 Testing model: {model}")
        try:
            response = requests.post(
                f"https://api-inference.huggingface.co/models/{model}",
                headers=headers,
                json={"inputs": test_prompt},
                timeout=30
            )
            
            print(f"📡 API Response Status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print("✅ API connection successful!")
                print(f"🤖 AI Response: {result[0]['generated_text'] if result else 'No response'}")
                return True, model
            elif response.status_code == 503:
                print("⚠️ Model is loading, this is normal for first request")
                return True, model
            else:
                print(f"❌ API Error: {response.status_code}")
                print(f"Response: {response.text[:200]}...")
                
        except Exception as e:
            print(f"❌ Connection failed: {e}")
    
    return False, None

@pytest.mark.asyncio
async def test_bot_tasks():
    """Test the specific tasks your bot uses."""
    print(f"\n🎮 Testing Bot-Specific Tasks")
    print("=" * 50)
    
    # First find a working model
    success, working_model = test_hf_connection()
    if not success:
        print("❌ No working model found, skipping bot-specific tests")
        return
    
    if not HF_API_KEY:
        print("❌ HF_API_KEY not found")
        return
    
    headers = {"Authorization": f"Bearer {HF_API_KEY}"}
    
    # Test 1: AI Riddle Task
    print("\n1️⃣ Testing AI Riddle Task")
    riddle_prompt = (
        "In a group game with players: Alice, Bob, Charlie.\n"
        "One player is secretly an impostor.\n"
        "Create a mysterious riddle or cryptic clue hinting at the impostor without naming them.\n"
        "Use metaphors or riddles only.\n"
        "Return the riddle and the 'answer' (the real player role or a hint)."
    )
    
    try:
        response = requests.post(
            f"https://api-inference.huggingface.co/models/{working_model}",
            headers=headers,
            json={"inputs": riddle_prompt},
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Riddle generated successfully!")
            print(f"🤖 AI Riddle: {result[0]['generated_text'] if result else 'No response'}")
        elif response.status_code == 503:
            print("⚠️ Model is still loading, this is normal")
        else:
            print(f"❌ Riddle generation failed: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Riddle test failed: {e}")
    
    # Test 2: Clue Generation
    print("\n2️⃣ Testing Clue Generation")
    clue_prompt = (
        "In a group game, one player is secretly an impostor. "
        "The players are: Alice, Bob, Charlie. "
        "Give a vague, mysterious clue about who the impostor might be without saying their name."
    )
    
    try:
        response = requests.post(
            f"https://api-inference.huggingface.co/models/{working_model}",
            headers=headers,
            json={"inputs": clue_prompt},
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Clue generated successfully!")
            print(f"🤖 AI Clue: {result[0]['generated_text'] if result else 'No response'}")
        elif response.status_code == 503:
            print("⚠️ Model is still loading, this is normal")
        else:
            print(f"❌ Clue generation failed: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Clue test failed: {e}")
    
    # Test 3: Complex Clue with History
    print("\n3️⃣ Testing Complex Clue with History")
    complex_prompt = (
        "In a group game, one player is secretly an impostor. "
        "The players are: Alice, Bob, Charlie. "
        "Recent discussion: Alice said she was working on the task, Bob was quiet, Charlie asked many questions. "
        "Give a mysterious, creative clue about who the impostor might be. "
        "You may use riddles, metaphors, or subtle hints, but never say the name directly."
    )
    
    try:
        response = requests.post(
            f"https://api-inference.huggingface.co/models/{working_model}",
            headers=headers,
            json={"inputs": complex_prompt},
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Complex clue generated successfully!")
            print(f"🤖 AI Complex Clue: {result[0]['generated_text'] if result else 'No response'}")
        elif response.status_code == 503:
            print("⚠️ Model is still loading, this is normal")
        else:
            print(f"❌ Complex clue generation failed: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Complex clue test failed: {e}")

def test_chat_interface():
    """Test a simple chat interface with the AI."""
    print(f"\n💬 Testing Chat Interface")
    print("=" * 50)
    
    # First find a working model
    success, working_model = test_hf_connection()
    if not success:
        print("❌ No working model found, skipping chat interface tests")
        return
    
    if not HF_API_KEY:
        print("❌ HF_API_KEY not found")
        return
    
    headers = {"Authorization": f"Bearer {HF_API_KEY}"}
    
    # Simple chat test
    chat_prompts = [
        "Hello, how are you today?",
        "Can you tell me a joke?",
        "What's the weather like?",
        "Tell me about yourself"
    ]
    
    for i, prompt in enumerate(chat_prompts, 1):
        print(f"\n{i}️⃣ Chat: {prompt}")
        
        try:
            response = requests.post(
                f"https://api-inference.huggingface.co/models/{working_model}",
                headers=headers,
                json={"inputs": prompt},
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                ai_response = result[0]['generated_text'] if result else 'No response'
                print(f"🤖 AI: {ai_response}")
            elif response.status_code == 503:
                print("⚠️ Model is loading...")
            else:
                print(f"❌ Error: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Chat failed: {e}")

def interactive_chat(working_model):
    """Interactive chat with the AI."""
    print(f"\n🎯 Interactive Chat Mode with {working_model}")
    print("=" * 50)
    print("Type your messages and press Enter. Type 'quit' to exit.")
    print("This simulates how your bot interacts with the AI.")
    
    if not HF_API_KEY:
        print("❌ HF_API_KEY not found")
        return
    
    headers = {"Authorization": f"Bearer {HF_API_KEY}"}
    
    while True:
        try:
            user_input = input("\n👤 You: ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("👋 Goodbye!")
                break
            
            if not user_input:
                continue
            
            print("🤖 AI is thinking...")
            
            response = requests.post(
                f"https://api-inference.huggingface.co/models/{working_model}",
                headers=headers,
                json={"inputs": user_input},
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                ai_response = result[0]['generated_text'] if result else 'I have no response.'
                print(f"🤖 AI: {ai_response}")
            elif response.status_code == 503:
                print("⚠️ Model is loading, please wait...")
            else:
                print(f"❌ Error: {response.status_code}")
                
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")

def main():
    """Main test function."""
    print("🤖 Hugging Face API Test")
    print("=" * 60)
    
    # Test 1: Basic connection
    success, working_model = test_hf_connection()
    
    if not success:
        print("\n❌ Cannot proceed without API connection")
        print("💡 This might be because:")
        print("   - The model is not available")
        print("   - The API key is invalid")
        print("   - There's a network issue")
        return
    
    print(f"\n✅ Using model: {working_model}")
    
    # Test 2: Bot-specific tasks
    asyncio.run(test_bot_tasks())
    
    # Test 3: Chat interface
    test_chat_interface()
    
    # Test 4: Interactive chat
    print("\n" + "=" * 60)
    choice = input("Would you like to try interactive chat? (y/n): ").strip().lower()
    
    if choice in ['y', 'yes']:
        interactive_chat(working_model)
    
    print("\n✅ Testing complete!")

if __name__ == "__main__":
    main() 