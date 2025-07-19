import unittest
from unittest.mock import patch, MagicMock
from bot.pulse_code import PulseCodeGame, AI_PERSONALITIES, generate_pulse_code

class TestPulseCodeGameAIVsPlayer(unittest.TestCase):

    def setUp(self):
        self.player_id = 123
        self.ai_id = -1
        self.chat_id = 456

    @patch('bot.llm_service.get_ai_guess')
    @patch('bot.llm_service.generate_ai_response')
    def test_ai_makes_guess_no_win(self, mock_generate_ai_response, mock_get_ai_guess):
        mock_generate_ai_response.return_value = "Mocked AI feedback."
        mock_get_ai_guess.return_value = "5678" # AI guesses incorrectly

        game = PulseCodeGame.setup_architect(self.player_id, "calculon")
        # Set player's code for AI to guess against
        player_state = game.players[self.player_id]
        player_state.code = "1234"

        # Ensure it's AI's turn to guess (setup_architect sets turn_order to [player_id, ai_id])
        game.current_turn = 1 # Set turn to AI

        result = game.ai_make_guess(self.ai_id, self.player_id)

        self.assertFalse(result["win"])
        self.assertEqual(result["guess"], "5678")
        self.assertEqual(result["hits"], 0)
        self.assertEqual(result["flashes"], 0)
        self.assertEqual(result["static"], 4)
        self.assertEqual(game.players[self.ai_id].stress, 40) # 4 static * 10 stress
        self.assertEqual(len(game.players[self.ai_id].guesses), 1)
        self.assertEqual(game.players[self.ai_id].guesses[0], "5678")
        self.assertEqual(len(game.history), 1)
        self.assertEqual(game.history[0]["guesser"], self.ai_id)
        self.assertEqual(game.history[0]["target"], self.player_id)
        self.assertTrue(game.active)
        self.assertIsNone(game.winner)

    @patch('bot.llm_service.get_ai_guess')
    @patch('bot.llm_service.generate_ai_response')
    def test_ai_makes_guess_win(self, mock_generate_ai_response, mock_get_ai_guess):
        mock_generate_ai_response.return_value = "Mocked AI feedback."
        mock_get_ai_guess.return_value = "1234" # AI guesses correctly

        game = PulseCodeGame.setup_architect(self.player_id, "calculon")
        # Set player's code for AI to guess against
        player_state = game.players[self.player_id]
        player_state.code = "1234"

        # Ensure it's AI's turn to guess
        game.current_turn = 1 # Set turn to AI

        result = game.ai_make_guess(self.ai_id, self.player_id)

        self.assertTrue(result["win"])
        self.assertEqual(result["guess"], "1234")
        self.assertEqual(result["hits"], 4)
        self.assertEqual(game.players[self.ai_id].stress, 0) # No static, no stress increase
        self.assertEqual(len(game.players[self.ai_id].guesses), 1)
        self.assertEqual(game.players[self.ai_id].guesses[0], "1234")
        self.assertEqual(len(game.history), 1)
        self.assertEqual(game.history[0]["guesser"], self.ai_id)
        self.assertEqual(game.history[0]["target"], self.player_id)
        self.assertFalse(game.active)
        self.assertEqual(game.winner, self.ai_id)

    @patch('bot.llm_service.get_ai_guess')
    @patch('bot.llm_service.generate_ai_response')
    def test_ai_makes_guess_invalid_fallback(self, mock_generate_ai_response, mock_get_ai_guess):
        mock_generate_ai_response.return_value = "Mocked AI feedback."
        mock_get_ai_guess.return_value = "1111" # AI returns an invalid guess

        game = PulseCodeGame.setup_architect(self.player_id, "calculon")
        player_state = game.players[self.player_id]
        player_state.code = "1234"
        game.current_turn = 1 # Set turn to AI

        # Patch generate_pulse_code to return a predictable valid code for fallback
        with patch('bot.pulse_code.generate_pulse_code', return_value="0987") as mock_gen_code:
            result = game.ai_make_guess(self.ai_id, self.player_id)
            mock_gen_code.assert_called_once() # Ensure fallback was used

        self.assertFalse(result["win"])
        self.assertEqual(result["guess"], "0987") # Should be the fallback code
        self.assertEqual(len(game.players[self.ai_id].guesses), 1)
        self.assertEqual(game.players[self.ai_id].guesses[0], "0987")

if __name__ == '__main__':
    unittest.main()