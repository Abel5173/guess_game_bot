import unittest
from bot.ai.dynamic_difficulty import get_difficulty_level, get_ai_guess_strategy

class TestDynamicDifficulty(unittest.TestCase):

    def test_get_difficulty_level(self):
        self.assertEqual(get_difficulty_level(900), "easy")
        self.assertEqual(get_difficulty_level(1000), "medium")
        self.assertEqual(get_difficulty_level(1100), "hard")

    def test_get_ai_guess_strategy(self):
        self.assertEqual(get_ai_guess_strategy("easy"), "random")
        self.assertEqual(get_ai_guess_strategy("medium"), "logical")
        self.assertEqual(get_ai_guess_strategy("hard"), "aggressive")

if __name__ == '__main__':
    unittest.main()
