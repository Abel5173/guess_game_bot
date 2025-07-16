def get_difficulty_level(skill_rating: int) -> str:
    """
    Determines the difficulty level based on the player's skill rating.
    """
    if skill_rating < 950:
        return "easy"
    elif 950 <= skill_rating < 1050:
        return "medium"
    else:
        return "hard"


def get_ai_guess_strategy(difficulty_level: str) -> str:
    """
    Determines the AI's guessing strategy based on the difficulty level.
    """
    if difficulty_level == "easy":
        return "random"
    elif difficulty_level == "medium":
        return "logical"
    else:
        return "aggressive"
