import random
import asyncio
from bot.utils import query_ai

async def ai_riddle_task(player_names, discussion_history=None):
    prompt = (
        f"In a group game with players: {', '.join(player_names)}.\n"
        "One player is secretly an impostor.\n"
        "Create a mysterious riddle or cryptic clue hinting at the impostor without naming them.\n"
        "Use metaphors or riddles only.\n"
        "Return the riddle and the 'answer' (the real player role or a hint)."
    )
    riddle = await query_ai(prompt)
    answer = "Think carefully who doesn't fit in..."
    return "ai_riddle", riddle, answer

def emoji_decode_task():
    emoji_puzzles = [
        ("🐱📦", "cat in the box"),
        ("👑🦁", "lion king"),
        ("🌞🌙", "day and night"),
        ("🔑🚪", "key door"),
        ("🐝🌸", "bee flower"),
    ]
    puzzle, answer = random.choice(emoji_puzzles)
    return "emoji_decode", f"Decode this emoji: {puzzle}", answer

def quick_math_task():
    math_puzzles = [
        ("What is 3 + 4 * 2?", "11"),
        ("If you have 5 apples and give 2 away, how many do you have?", "3"),
        ("What number comes next: 2, 4, 6, ?", "8"),
    ]
    puzzle, answer = random.choice(math_puzzles)
    return "quick_math", puzzle, answer

def word_unscramble_task():
    words = [
        ("tca", "cat"),
        ("odg", "dog"),
        ("esuohr", "shower"),
        ("lpepa", "apple"),
        ("nial", "nail"),
    ]
    scrambled, answer = random.choice(words)
    return "word_unscramble", f"Unscramble this word: {scrambled}", answer

def trivia_task():
    trivia = [
        ("What planet is known as the Red Planet?", "mars"),
        ("Who wrote 'Romeo and Juliet'?", "shakespeare"),
        ("What is the largest mammal?", "blue whale"),
    ]
    question, answer = random.choice(trivia)
    return "trivia", question, answer

def pattern_recognition_task():
    patterns = [
        ("What comes next: A, C, E, G, ?", "i"),
        ("What comes next: 1, 4, 9, 16, ?", "25"),
        ("What comes next: Mon, Wed, Fri, ?", "sun"),
    ]
    question, answer = random.choice(patterns)
    return "pattern_recognition", question, answer

async def get_random_task(player_names, discussion_history=None):
    task_funcs = [
        lambda: ai_riddle_task(player_names, discussion_history),
        lambda: asyncio.to_thread(emoji_decode_task),
        lambda: asyncio.to_thread(quick_math_task),
        lambda: asyncio.to_thread(word_unscramble_task),
        lambda: asyncio.to_thread(trivia_task),
        lambda: asyncio.to_thread(pattern_recognition_task),
    ]
    task_func = random.choice(task_funcs)
    return await task_func() 