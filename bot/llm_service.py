import os
import requests
import logging
from dotenv import load_dotenv
import random

logger = logging.getLogger(__name__)
load_dotenv()

API_URL = "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.1"
API_KEY = os.getenv("HUGGINGFACE_API_KEY")

def generate_ai_response(prompt: str) -> str:
    """
    Generates a response from the Hugging Face Inference API.
    """
    if not API_KEY:
        logger.warning("HUGGINGFACE_API_KEY not found. Returning a default response.")
        return "AI is currently offline. Default response."

    headers = {"Authorization": f"Bearer {API_KEY}"}
    payload = {
        "inputs": prompt,
        "parameters": {
            "max_new_tokens": 100,
            "temperature": 0.8,
            "top_p": 0.9,
            "repetition_penalty": 1.2,
        },
        "options": {
            "wait_for_model": True
        }
    }

    try:
        response = requests.post(API_URL, headers=headers, json=payload, timeout=20)
        response.raise_for_status()  # Raise an exception for bad status codes
        
        generated_text = response.json()[0].get("generated_text", "")
        
        # Clean the response to remove the initial prompt
        if prompt in generated_text:
            generated_text = generated_text.replace(prompt, "").strip()
            
        # Further cleaning for instruction-tuned models
        if "[/INST]" in generated_text:
            generated_text = generated_text.split("[/INST]")[-1].strip()
            
        logger.info(f"LLM generated response: {generated_text}")
        return generated_text if generated_text else "The AI seems to be at a loss for words."

    except requests.exceptions.RequestException as e:
        logger.error(f"Error calling Hugging Face API: {e}")
        return "The AI is experiencing technical difficulties."
    except (KeyError, IndexError) as e:
        logger.error(f"Error parsing Hugging Face API response: {e}")
        return "The AI's response was garbled."

def get_ai_guess(history: list[tuple[str, int, int]]) -> str:
    """
    Gets an AI guess for the Pulse Code game based on the history of previous guesses.
    """
    # Format the history for the prompt
    formatted_history = "\n".join([f"Guess: {g}, Pulses: {p}, Echoes: {e}" for g, p, e in history])
    
    prompt = f'''
[INST] You are an expert player in a code-breaking game called Pulse Code.
The goal is to guess a 4-digit secret code with no repeating digits.
- "Pulses" are correct digits in the correct position.
- "Echoes" are correct digits in the wrong position.

Based on the following game history, what is the most logical next guess?
Your response should be ONLY the 4-digit code.

History:
{formatted_history}

Logical next guess:
[/INST]
'''
    
    response = generate_ai_response(prompt)
    
    # Basic validation to ensure the response is a 4-digit number
    if response.isdigit() and len(response) == 4:
        return response
    else:
        logger.warning(f"LLM returned an invalid guess: '{response}'. Falling back to a random guess.")
        # Fallback to a simple random guess if the LLM fails
        return "".join(random.sample("0123456789", 4))
