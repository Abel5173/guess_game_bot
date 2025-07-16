"""
Arcade Mode System - Mini-games between rounds for engagement.
"""

import random
import asyncio
from typing import Dict, List, Optional, Tuple
from enum import Enum
from datetime import datetime, timedelta
from bot.database import SessionLocal
from bot.database.models import Player
import logging

logger = logging.getLogger(__name__)


class ArcadeGameType(Enum):
    QUICK_MATH = "quick_math"
    EMOJI_GUESS = "emoji_guess"
    WORD_SCRAMBLE = "word_scramble"
    MEMORY_GAME = "memory_game"
    RIDDLE_CHALLENGE = "riddle_challenge"
    SPEED_TYPING = "speed_typing"


class ArcadeSystem:
    """Manages arcade mini-games between rounds."""

    def __init__(self):
        self.active_games = {}  # session_id -> arcade_game_data
        self.player_scores = {}  # session_id -> {player_id -> score}
        self.game_definitions = {
            ArcadeGameType.QUICK_MATH: {
                "name": "Quick Math",
                "description": "Solve math problems quickly!",
                "duration": 30,  # seconds
                "max_players": 10,
                "xp_reward": 20,
            },
            ArcadeGameType.EMOJI_GUESS: {
                "name": "Emoji Guess",
                "description": "Guess the word from emojis!",
                "duration": 45,
                "max_players": 10,
                "xp_reward": 25,
            },
            ArcadeGameType.WORD_SCRAMBLE: {
                "name": "Word Scramble",
                "description": "Unscramble the word!",
                "duration": 60,
                "max_players": 10,
                "xp_reward": 30,
            },
            ArcadeGameType.MEMORY_GAME: {
                "name": "Memory Game",
                "description": "Remember the sequence!",
                "duration": 40,
                "max_players": 8,
                "xp_reward": 35,
            },
            ArcadeGameType.RIDDLE_CHALLENGE: {
                "name": "Riddle Challenge",
                "description": "Solve the riddle!",
                "duration": 90,
                "max_players": 10,
                "xp_reward": 40,
            },
            ArcadeGameType.SPEED_TYPING: {
                "name": "Speed Typing",
                "description": "Type the phrase quickly!",
                "duration": 30,
                "max_players": 10,
                "xp_reward": 25,
            },
        }

        # Game content pools
        self.math_problems = [
            ("5 + 7 × 2", "19"),
            ("12 ÷ 3 + 8", "12"),
            ("15 - 6 × 2", "3"),
            ("20 ÷ 4 + 5", "10"),
            ("8 + 3 × 4", "20"),
            ("16 ÷ 2 - 3", "5"),
            ("9 + 6 ÷ 2", "12"),
            ("14 - 4 × 2", "6"),
        ]

        self.emoji_puzzles = [
            ("🐱🐕🐦", "pets"),
            ("🍕🍔🌮", "food"),
            ("⚽🏀🏈", "sports"),
            ("🌞🌙⭐", "space"),
            ("🚗✈️🚢", "transport"),
            ("🎵🎬🎮", "entertainment"),
            ("🌺🌸🌻", "flowers"),
            ("🏠🏢🏰", "buildings"),
        ]

        self.scrambled_words = [
            ("impostor", "impostor"),
            ("crewmate", "crewmate"),
            ("detective", "detective"),
            ("sabotage", "sabotage"),
            ("emergency", "emergency"),
            ("suspicious", "suspicious"),
            ("evidence", "evidence"),
            ("victory", "victory"),
        ]

        self.riddles = [
            (
                "I speak without a mouth and hear without ears. I have no body, but I come alive with wind. What am I?",
                "echo",
            ),
            (
                "What has keys, but no locks; space, but no room; and you can enter, but not go in?",
                "keyboard",
            ),
            ("The more you take, the more you leave behind. What am I?", "footsteps"),
            ("What gets wetter and wetter the more it dries?", "towel"),
            ("What has a head and a tail but no body?", "coin"),
            (
                "What comes once in a minute, twice in a moment, but never in a thousand years?",
                "m",
            ),
            ("What is always in front of you but can't be seen?", "future"),
            ("What breaks when you say it?", "silence"),
        ]

        self.typing_phrases = [
            "The quick brown fox jumps over the lazy dog",
            "All work and no play makes Jack a dull boy",
            "To be or not to be that is the question",
            "A journey of a thousand miles begins with a single step",
            "Actions speak louder than words",
            "Better late than never",
            "Don't judge a book by its cover",
            "Every cloud has a silver lining",
        ]

    def start_arcade_game(
        self, session_id: int, game_type: ArcadeGameType = None
    ) -> Dict:
        """Start a new arcade game in a session."""
        if game_type is None:
            game_type = random.choice(list(ArcadeGameType))

        if session_id in self.active_games:
            return {"error": "Arcade game already in progress"}

        game_def = self.game_definitions[game_type]

        # Generate game content
        game_content = self._generate_game_content(game_type)

        # Initialize game state
        game_data = {
            "type": game_type,
            "name": game_def["name"],
            "description": game_def["description"],
            "content": game_content,
            "answer": game_content["answer"],
            "start_time": datetime.now(),
            "end_time": datetime.now() + timedelta(seconds=game_def["duration"]),
            "duration": game_def["duration"],
            "max_players": game_def["max_players"],
            "xp_reward": game_def["xp_reward"],
            "players": [],
            "answers": {},
            "winners": [],
        }

        self.active_games[session_id] = game_data

        # Initialize scores
        if session_id not in self.player_scores:
            self.player_scores[session_id] = {}

        logger.info(f"Started arcade game {game_type.value} in session {session_id}")

        return game_data

    def join_arcade_game(self, session_id: int, player_id: int) -> Tuple[bool, str]:
        """Join an active arcade game."""
        if session_id not in self.active_games:
            return False, "❌ No active arcade game"

        game = self.active_games[session_id]

        if datetime.now() > game["end_time"]:
            return False, "⏰ Game has already ended"

        if player_id in game["players"]:
            return False, "❌ You're already in this game"

        if len(game["players"]) >= game["max_players"]:
            return False, "❌ Game is full"

        game["players"].append(player_id)

        return True, f"✅ Joined {game['name']}!"

    def submit_answer(
        self, session_id: int, player_id: int, answer: str
    ) -> Tuple[bool, str]:
        """Submit an answer to the current arcade game."""
        if session_id not in self.active_games:
            return False, "❌ No active arcade game"

        game = self.active_games[session_id]

        if datetime.now() > game["end_time"]:
            return False, "⏰ Game has already ended"

        if player_id not in game["players"]:
            return False, "❌ You're not in this game"

        if player_id in game["answers"]:
            return False, "❌ You've already submitted an answer"

        # Check if answer is correct
        is_correct = self._check_answer(game["type"], answer, game["answer"])

        game["answers"][player_id] = {
            "answer": answer,
            "correct": is_correct,
            "submitted_at": datetime.now(),
        }

        if is_correct:
            game["winners"].append(player_id)
            return True, "✅ Correct answer! You're a winner!"
        else:
            return False, "❌ Wrong answer. Try again!"

    def get_game_status(self, session_id: int) -> Dict:
        """Get current status of arcade game."""
        if session_id not in self.active_games:
            return {"error": "No active arcade game"}

        game = self.active_games[session_id]
        time_left = (game["end_time"] - datetime.now()).total_seconds()

        return {
            "type": game["type"].value,
            "name": game["name"],
            "description": game["description"],
            "content": game["content"],
            "time_left": max(0, int(time_left)),
            "players_count": len(game["players"]),
            "max_players": game["max_players"],
            "answers_count": len(game["answers"]),
            "winners_count": len(game["winners"]),
            "xp_reward": game["xp_reward"],
        }

    def end_arcade_game(self, session_id: int) -> Dict:
        """End the current arcade game and award prizes."""
        if session_id not in self.active_games:
            return {"error": "No active arcade game"}

        game = self.active_games[session_id]
        results = {
            "game_type": game["type"].value,
            "game_name": game["name"],
            "total_players": len(game["players"]),
            "winners": game["winners"],
            "winners_count": len(game["winners"]),
            "xp_reward": game["xp_reward"],
        }

        # Award XP to winners
        for winner_id in game["winners"]:
            self._award_arcade_xp(winner_id, game["xp_reward"])

        # Update session scores
        if session_id not in self.player_scores:
            self.player_scores[session_id] = {}

        for winner_id in game["winners"]:
            if winner_id not in self.player_scores[session_id]:
                self.player_scores[session_id][winner_id] = 0
            self.player_scores[session_id][winner_id] += game["xp_reward"]

        # Clean up
        del self.active_games[session_id]

        logger.info(
            f"Ended arcade game in session {session_id}: {len(game['winners'])} winners"
        )

        return results

    def get_session_scores(self, session_id: int) -> Dict:
        """Get arcade scores for a session."""
        return self.player_scores.get(session_id, {})

    def generate_arcade_menu(self) -> str:
        """Generate a menu showing available arcade games."""
        menu = "🎮 **Arcade Mode**\n\n"
        menu += "**Available Mini-Games:**\n\n"

        for game_type, game_def in self.game_definitions.items():
            menu += f"🎯 **{game_def['name']}**\n"
            menu += f"   {game_def['description']}\n"
            menu += f"   Duration: {game_def['duration']}s | XP: {game_def['xp_reward']}\n\n"

        menu += "**How it works:**\n"
        menu += "• Games start automatically between rounds\n"
        menu += "• Quick mini-games to keep you engaged\n"
        menu += "• Win XP rewards for correct answers\n"
        menu += "• Compete with other players!"

        return menu

    def _generate_game_content(self, game_type: ArcadeGameType) -> Dict:
        """Generate content for a specific game type."""
        if game_type == ArcadeGameType.QUICK_MATH:
            problem, answer = random.choice(self.math_problems)
            return {
                "question": f"Solve: {problem}",
                "answer": answer,
                "hint": "Remember order of operations!",
            }

        elif game_type == ArcadeGameType.EMOJI_GUESS:
            emojis, word = random.choice(self.emoji_puzzles)
            return {
                "question": f"What word do these emojis represent?\n{emojis}",
                "answer": word,
                "hint": "Think about what these emojis have in common",
            }

        elif game_type == ArcadeGameType.WORD_SCRAMBLE:
            original, answer = random.choice(self.scrambled_words)
            scrambled = "".join(random.sample(original, len(original)))
            return {
                "question": f"Unscramble: {scrambled}",
                "answer": answer,
                "hint": "It's related to our game!",
            }

        elif game_type == ArcadeGameType.RIDDLE_CHALLENGE:
            riddle, answer = random.choice(self.riddles)
            return {
                "question": riddle,
                "answer": answer,
                "hint": "Think outside the box!",
            }

        elif game_type == ArcadeGameType.SPEED_TYPING:
            phrase = random.choice(self.typing_phrases)
            return {
                "question": f'Type this phrase exactly:\n"{phrase}"',
                "answer": phrase.lower(),
                "hint": "Be careful with spelling and punctuation!",
            }

        else:  # MEMORY_GAME
            sequence = "".join(random.choices("123456789", k=4))
            return {
                "question": f"Remember this sequence: {sequence}",
                "answer": sequence,
                "hint": "Focus and memorize!",
            }

    def _check_answer(
        self, game_type: ArcadeGameType, player_answer: str, correct_answer: str
    ) -> bool:
        """Check if a player's answer is correct."""
        # Normalize answers for comparison
        player_clean = player_answer.lower().strip()
        correct_clean = correct_answer.lower().strip()

        if game_type == ArcadeGameType.SPEED_TYPING:
            # For typing games, be more lenient with spacing
            player_clean = " ".join(player_clean.split())
            correct_clean = " ".join(correct_clean.split())

        return player_clean == correct_clean

    def _award_arcade_xp(self, player_id: int, xp_amount: int):
        """Award XP to a player for arcade game success."""
        db = SessionLocal()
        try:
            player = db.query(Player).filter(Player.id == player_id).first()
            if player:
                player.xp += xp_amount
                db.commit()
                logger.info(
                    f"Player {player_id} earned {xp_amount} XP from arcade game"
                )
        except Exception as e:
            logger.error(f"Failed to award arcade XP: {e}")
            db.rollback()
        finally:
            db.close()

    def cleanup_session_arcade(self, session_id: int):
        """Clean up arcade data for a finished session."""
        if session_id in self.active_games:
            del self.active_games[session_id]

        if session_id in self.player_scores:
            del self.player_scores[session_id]

        logger.info(f"Cleaned up arcade data for session {session_id}")


# Global instance
arcade_system = ArcadeSystem()
