import os
import requests
import asyncio
from dotenv import load_dotenv
from tenacity import retry, stop_after_attempt, wait_fixed

load_dotenv()
HF_API_KEY = os.getenv("HF_API_KEY")
TOKEN = os.getenv("BOT_TOKEN")

@retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
async def query_ai(prompt):
    headers = {"Authorization": f"Bearer {HF_API_KEY}"}
    payload = {"inputs": prompt}
    try:
        response = requests.post(
            "https://api-inference.huggingface.co/models/microsoft/DialoGPT-medium",
            headers=headers,
            json=payload
        )
        if response.status_code == 200:
            result = response.json()
            return result[0]['generated_text'] if result else "🤖 I have no words!"
        else:
            return "⚠️ AI is feeling shy. Try again later."
    except Exception as e:
        return f"❌ Error: {e}"

def sync_generate_clue(player_names):
    prompt = (
        f"In a group game, one player is secretly an impostor. "
        f"The players are: {', '.join(player_names)}. "
        "Give a vague, mysterious clue about who the impostor might be without saying their name."
    )
    headers = {"Authorization": f"Bearer {HF_API_KEY}"}
    response = requests.post(
        "https://api-inference.huggingface.co/models/microsoft/DialoGPT-medium",
        headers=headers,
        json={"inputs": prompt}
    )
    if response.status_code == 200:
        result = response.json()
        return result[0]['generated_text'] if result else "🤖 AI has no clue this time."
    return "🤖 I'm stumped... try again later."

async def generate_clue(player_names):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, sync_generate_clue, player_names)

async def generate_complex_clue(player_names, history=None):
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