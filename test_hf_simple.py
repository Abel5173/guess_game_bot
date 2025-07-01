#!/usr/bin/env python3
"""
Simple test to check Hugging Face Chat Completion API.
"""

import os
from huggingface_hub import InferenceClient
from dotenv import load_dotenv

load_dotenv()
HF_API_KEY = os.getenv("HF_API_KEY")

def test_chat_completion():
    """Test Chat Completion API with different models."""
    print("🔍 Testing Hugging Face Chat Completion API")
    print("=" * 50)
    
    if not HF_API_KEY:
        print("❌ HF_API_KEY not found")
        return False, None
    
    print(f"✅ HF_API_KEY found: {HF_API_KEY[:10]}...")
    
    # Models that support chat completion
    chat_models = [
        "sarvamai/sarvam-m",
        "microsoft/DialoGPT-medium",
        "microsoft/DialoGPT-small",
        "microsoft/DialoGPT-large",
        "HuggingFaceH4/zephyr-7b-beta",
        "meta-llama/Llama-2-7b-chat-hf",
        "tiiuae/falcon-7b-instruct",
        "bigscience/bloomz-560m"
    ]
    
    client = InferenceClient(
        provider="hf-inference",
        api_key=HF_API_KEY,
    )
    
    for model in chat_models:
        print(f"\n🔍 Testing Chat Model: {model}")
        try:
            completion = client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "user",
                        "content": "Hello! How are you today?"
                    }
                ],
            )
            
            print("✅ Chat completion successful!")
            print(f"🤖 AI Response: {completion.choices[0].message.content}")
            return True, model
            
        except Exception as e:
            print(f"❌ Error with {model}: {str(e)[:100]}...")
    
    return False, None

def test_bot_specific_chat():
    """Test bot-specific prompts with chat completion."""
    print(f"\n🎮 Testing Bot-Specific Chat")
    print("=" * 50)
    
    # First find a working model
    success, working_model = test_chat_completion()
    if not success:
        print("❌ No working model found, skipping bot-specific tests")
        return
    
    client = InferenceClient(
        provider="hf-inference",
        api_key=HF_API_KEY,
    )
    
    # Test 1: Riddle generation
    print("\n1️⃣ Testing Riddle Generation")
    try:
        completion = client.chat.completions.create(
            model=working_model,
            messages=[
                {
                    "role": "user",
                    "content": "In a group game with players: Alice, Bob, Charlie. One player is secretly an impostor. Create a mysterious riddle hinting at the impostor without naming them."
                }
            ],
        )
        
        print("✅ Riddle generated!")
        print(f"🤖 AI Riddle: {completion.choices[0].message.content}")
        
    except Exception as e:
        print(f"❌ Riddle generation failed: {e}")
    
    # Test 2: Clue generation
    print("\n2️⃣ Testing Clue Generation")
    try:
        completion = client.chat.completions.create(
            model=working_model,
            messages=[
                {
                    "role": "user",
                    "content": "In a group game, one player is secretly an impostor. The players are: Alice, Bob, Charlie. Give a vague, mysterious clue about who the impostor might be without saying their name."
                }
            ],
        )
        
        print("✅ Clue generated!")
        print(f"🤖 AI Clue: {completion.choices[0].message.content}")
        
    except Exception as e:
        print(f"❌ Clue generation failed: {e}")

def interactive_chat(working_model):
    """Interactive chat with the AI."""
    print(f"\n🎯 Interactive Chat Mode with {working_model}")
    print("=" * 50)
    print("Type your messages and press Enter. Type 'quit' to exit.")
    print("This simulates how your bot interacts with the AI.")
    
    client = InferenceClient(
        provider="hf-inference",
        api_key=HF_API_KEY,
    )
    
    while True:
        try:
            user_input = input("\n👤 You: ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("👋 Goodbye!")
                break
            
            if not user_input:
                continue
            
            print("🤖 AI is thinking...")
            
            completion = client.chat.completions.create(
                model=working_model,
                messages=[
                    {
                        "role": "user",
                        "content": user_input
                    }
                ],
            )
            
            ai_response = completion.choices[0].message.content
            print(f"🤖 AI: {ai_response}")
                
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")

def main():
    print("🤖 Hugging Face Chat Completion API Test")
    print("=" * 60)
    
    # Test chat completion
    success, model = test_chat_completion()
    
    if not success:
        print("\n❌ Chat completion test failed")
        print("💡 This might be because:")
        print("   - The models require special access")
        print("   - Your API key doesn't have chat completion permissions")
        print("   - The models are not available for your account")
        return
    
    print(f"\n✅ Found working chat model: {model}")
    
    # Test bot-specific functionality
    test_bot_specific_chat()
    
    # Interactive chat
    print("\n" + "=" * 60)
    choice = input("Would you like to try interactive chat? (y/n): ").strip().lower()
    
    if choice in ['y', 'yes']:
        interactive_chat(model)
    
    print("\n✅ Testing complete!")

if __name__ == "__main__":
    main() 