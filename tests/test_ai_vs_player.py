import unittest
from unittest.mock import patch
from game.ai_vs_player import AIVsPlayerGame

class TestAIVsPlayerGame(unittest.TestCase):
    def setUp(self):
        self.game = AIVsPlayerGame(player_id="test_player")
        self.game.set_player_code("1234")

    def test_initialization(self):
        self.assertEqual(self.game.player_id, "test_player")
        self.assertIsNotNone(self.game.ai_code)
        self.assertEqual(self.game.turn, "player")
        self.assertFalse(self.game.ended)

    def test_set_player_code(self):
        self.assertTrue(self.game.set_player_code("5678"))
        self.assertEqual(self.game.player_code, "5678")
        self.assertFalse(self.game.set_player_code("1122"))  # Invalid
        self.assertFalse(self.game.set_player_code("123"))  # Invalid

    def test_player_guess_correct(self):
        self.game.ai_code = "1234"
        result = self.game.player_guess("1234")
        self.assertTrue(result["win"])
        self.assertEqual(result["pulses"], 4)
        self.assertTrue(self.game.ended)
        self.assertEqual(self.game.winner, "player")

    def test_player_guess_incorrect(self):
        self.game.ai_code = "1234"
        result = self.game.player_guess("5678")
        self.assertFalse(result["win"])
        self.assertEqual(self.game.turn, "ai")

    @patch("game.ai_vs_player.get_ai_guess")
    def test_ai_guess_correct(self, mock_get_ai_guess):
        mock_get_ai_guess.return_value = "1234"
        result = self.game.ai_guess()
        self.assertTrue(result["win"])
        self.assertEqual(result["pulses"], 4)
        self.assertTrue(self.game.ended)
        self.assertEqual(self.game.winner, "ai")

    @patch("game.ai_vs_player.get_ai_guess")
    def test_ai_guess_incorrect(self, mock_get_ai_guess):
        mock_get_ai_guess.return_value = "5678"
        result = self.game.ai_guess()
        self.assertFalse(result["win"])
        self.assertEqual(self.game.turn, "player")

    def test_game_draw(self):
        self.game.max_turns = 2
        self.game.player_guess("5678")
        with patch("game.ai_vs_player.get_ai_guess") as mock_get_ai_guess:
            mock_get_ai_guess.return_value = "5678"
            self.game.ai_guess()
        self.assertTrue(self.game.ended)
        self.assertEqual(self.game.winner, "draw")

    @patch("game.ai_vs_player.get_ai_guess")
    def test_ai_strategy(self, mock_get_ai_guess):
        mock_get_ai_guess.return_value = "1234"
        self.game.player_guess("5678")
        result = self.game.ai_guess()
        self.assertEqual(result["guess"], "1234")

if __name__ == "__main__":
    unittest.main()
