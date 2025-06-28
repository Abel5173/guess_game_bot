# Impostor-game-specific helper functions will go here.
from typing import List, Tuple

TITLE_THRESHOLDS: List[Tuple[int, str]] = [
    (0, "Rookie"),
    (30, "Apprentice"),
    (60, "Sleuth"),
    (120, "Veteran"),
    (200, "Mastermind"),
    (300, "Legend"),
]


def calculate_title(xp: int) -> str:
    for xp_threshold, title in reversed(TITLE_THRESHOLDS):
        if xp >= xp_threshold:
            return title
    return "Rookie"
