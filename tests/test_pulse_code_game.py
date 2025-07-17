import unittest
from bot.pulse_code.core import PulseCodeGame


class TestPulseCodeGame(unittest.TestCase):

    def setUp(self):
        self.game = PulseCodeGame(host_id=123, chat_id=456)
        self.game.start_game()

    def test_pulse_code_generation(self):
        code = self.game._generate_pulse_code()
        self.assertEqual(len(code), 4)
        self.assertTrue(code.isdigit())
        self.assertEqual(len(set(code)), 4)

    def test_make_guess(self):
        self.game.ai_opponents["AI-Calculon"]["code"] = "1234"

        # Test a correct guess
        hits, flashes, static = self.game.make_guess(
            player_id=123, target_id="AI-Calculon", guess="1234"
        )
        self.assertEqual(hits, 4)
        self.assertEqual(flashes, 0)
        self.assertEqual(static, 0)

        # Test a guess with some hits and flashes
        hits, flashes, static = self.game.make_guess(
            player_id=123, target_id="AI-Calculon", guess="1325"
        )
        self.assertEqual(hits, 1)
        self.assertEqual(flashes, 2)
        self.assertEqual(static, 1)

        # Test a guess with only flashes
        hits, flashes, static = self.game.make_guess(
            player_id=123, target_id="AI-Calculon", guess="4321"
        )
        self.assertEqual(hits, 0)
        self.assertEqual(flashes, 4)
        self.assertEqual(static, 0)

        # Test a guess with only static
        hits, flashes, static = self.game.make_guess(
            player_id=123, target_id="AI-Calculon", guess="5678"
        )
        self.assertEqual(hits, 0)
        self.assertEqual(flashes, 0)
        self.assertEqual(static, 4)

    def test_invalid_guess(self):
        with self.assertRaises(ValueError):
            self.game.make_guess(player_id=123, target_id="AI-Calculon", guess="123")
        with self.assertRaises(ValueError):
            self.game.make_guess(player_id=123, target_id="AI-Calculon", guess="123a")
        with self.assertRaises(ValueError):
            self.game.make_guess(player_id=123, target_id="AI-Calculon", guess="1223")


if __name__ == "__main__":
    unittest.main()
