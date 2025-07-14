import pytest
from bot.pulse_code.core import PulseCodeCore

def test_pulse_code_generation():
    core = PulseCodeCore()
    code = core.generate_pulse_code()
    assert len(code) == 4
    assert len(set(code)) == 4

def test_guess_feedback():
    core = PulseCodeCore()
    core.add_player(1, "Test Player")
    core.players[1]['pulse_code'] = [1, 2, 3, 4]

    # Mocking the AI opponent for the guess
    core.add_ai_opponent("PulseCodeBot", "The Calculon")
    core.ai_opponents["PulseCodeBot"]['pulse_code'] = [1, 2, 3, 4]


    # Perfect guess
    hits, flashes, static = core.make_guess(1, "PulseCodeBot", [1, 2, 3, 4])
    assert (hits, flashes, static) == (4, 0, 0)

    # All flashes
    hits, flashes, static = core.make_guess(1, "PulseCodeBot", [4, 3, 2, 1])
    assert (hits, flashes, static) == (0, 4, 0)

    # All static
    hits, flashes, static = core.make_guess(1, "PulseCodeBot", [5, 6, 7, 8])
    assert (hits, flashes, static) == (0, 0, 4)

    # Mixed
    hits, flashes, static = core.make_guess(1, "PulseCodeBot", [1, 4, 7, 2])
    assert (hits, flashes, static) == (1, 2, 1)
