import os
import asyncio
from typing import List, Optional, Any
from dotenv import load_dotenv
from tenacity import retry, stop_after_attempt, wait_fixed
from huggingface_hub import InferenceClient

load_dotenv()
HF_API_KEY = os.getenv("HF_API_KEY")
TOKEN = os.getenv("BOT_TOKEN")

# Initialize the Hugging Face client
client = InferenceClient(
    model="mistralai/Mistral-7B-Instruct-v0.1",
    token=HF_API_KEY,
)

@retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
async def query_ai(prompt: str) -> str:
    """Query AI using Chat Completion API."""
    try:
        completion = client.chat.completions.create(
            model="sarvamai/sarvam-m",  # Using the working model we found
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
        )
        return completion.choices[0].message.content
    except Exception as e:
        return f"❌ Error: {e}"


def sync_generate_clue(player_names: List[str]) -> str:
    """Generate a clue using Chat Completion API (sync version)."""
    prompt = (
        f"In a group game, one player is secretly an impostor. "
        f"The players are: {', '.join(player_names)}. "
        "Give a vague, mysterious clue about who the impostor might be without saying their name."
    )
    try:
        completion = client.chat.completions.create(
            model="sarvamai/sarvam-m",
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
        )
        return completion.choices[0].message.content
    except Exception as e:
        return f"🤖 Error generating clue: {e}"


async def generate_clue(player_names: List[str]) -> str:
    """Generate a clue asynchronously."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, sync_generate_clue, player_names)


async def generate_complex_clue(
    player_names: List[str], history: Optional[str] = None
) -> str:
    """Generate a complex clue with discussion history."""
    prompt = (
        f"In a group game, one player is secretly an impostor. "
        f"The players are: {', '.join(player_names)}. "
    )
    if history:
        prompt += f"Recent discussion: {history}. "
    prompt += (
        "Give a mysterious, creative clue about who the impostor might be. "
        "You may use riddles, metaphors, or subtle hints, but never say the name directly."
    )
    return await query_ai(prompt)
