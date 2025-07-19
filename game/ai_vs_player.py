import random
from itertools import permutations
import json
from bot.llm_service import get_ai_guess

class AIVsPlayerGame:
    """
    Bulls and Cows (Pulses/Echoes) AI vs Player game logic.
    Handles code setup, turn management, guess validation, scoring, AI strategy, XP, and win/draw logic.
    """
    def __init__(self, player_id, max_turns=10):
        self.player_id = player_id
        self.player_code = None
        self.ai_code = self._generate_code()
        self.turn = 'player'  # or 'ai'
        self.history = []  # (turn, guess, pulses, echoes)
        self.ai_possible_codes = self._all_possible_codes()
        self.ai_last_guess = None
        self.xp = {player_id: 0, 'ai': 0}
        self.max_turns = max_turns
        self.turn_count = 0
        self.ended = False
        self.winner = None

    def set_player_code(self, code):
        """Set and validate the player's secret code."""
        if self._is_valid_code(code):
            self.player_code = code
            return True
        return False

    def player_guess(self, guess):
        """Player guesses AI's code. Returns result dict."""
        if self.ended:
            return {'error': 'Game has already ended.'}
        pulses, echoes = self._score_guess(guess, self.ai_code)
        self.history.append(('player', guess, pulses, echoes))
        self.turn_count += 1
        if pulses == 4:
            self.xp[self.player_id] += 10
            self.ended = True
            self.winner = 'player'
            return {'win': True, 'pulses': pulses, 'echoes': echoes}
        if self.turn_count >= self.max_turns:
            self.ended = True
            self.winner = 'draw'
            return {'win': False, 'pulses': pulses, 'echoes': echoes}
        self.turn = 'ai'
        return {'win': False, 'pulses': pulses, 'echoes': echoes}

    def ai_guess(self):
        """AI guesses player's code. Returns result dict."""
        if self.ended:
            return {'error': 'Game has already ended.'}
        ai_history = [(g, p, e) for turn, g, p, e in self.history if turn == 'ai']
        guess = self._ai_strategy(ai_history)
        pulses, echoes = self._score_guess(guess, self.player_code)
        self.history.append(('ai', guess, pulses, echoes))
        
        win = pulses == 4
        if win:
            self.xp['ai'] += 10
            self.ended = True
            self.winner = 'ai'
            
        self.turn_count += 1
        if self.turn_count >= self.max_turns:
            self.ended = True
            self.winner = 'draw'
        
        self.turn = 'player'
        return {'win': win, 'guess': guess, 'pulses': pulses, 'echoes': echoes}

    def _generate_code(self):
        digits = random.sample('0123456789', 4)
        return ''.join(digits)

    def _is_valid_code(self, code):
        return len(code) == 4 and code.isdigit() and len(set(code)) == 4

    def _score_guess(self, guess, code):
        pulses = sum(a == b for a, b in zip(guess, code))
        echoes = sum(min(guess.count(d), code.count(d)) for d in set(guess)) - pulses
        return pulses, echoes

    def _all_possible_codes(self):
        return [''.join(p) for p in permutations('0123456789', 4)]

    def _ai_strategy(self, history):
        """AI strategy that uses LLM to make a guess."""
        if not history:
            # First guess can be random or a fixed one like '1234'
            guess = "1234"
        else:
            guess = get_ai_guess(history)
        
        self.ai_last_guess = guess
        # Filter out the current guess from possible codes
        if guess in self.ai_possible_codes:
            self.ai_possible_codes.remove(guess)
        return guess

    def get_leaderboard_entry(self):
        return {self.player_id: self.xp[self.player_id], 'ai': self.xp['ai']}

    def get_history(self):
        return self.history

    def is_ended(self):
        return self.ended

    def get_winner(self):
        return self.winner 

class PvPGameSession:
    """
    Player vs Player Bulls and Cows game session.
    Handles code setup, turn management, guess validation, scoring, XP, win count, and session state.
    XP and win count are JSON-serializable.
    """
    def __init__(self, player1_id, player2_id, max_turns=20):
        self.player1_id = player1_id
        self.player2_id = player2_id
        self.codes = {}  # user_id: code
        self.guesses = {player1_id: [], player2_id: []}
        self.turn = player1_id  # player1 starts
        self.max_turns = max_turns
        self.turn_count = 0
        self.ended = False
        self.winner = None
        self.xp = {player1_id: 0, player2_id: 0}
        self.wins = {player1_id: 0, player2_id: 0}
        self.streaks = {player1_id: 0, player2_id: 0}  # win streaks
        self.power_ups = {player1_id: {"reveal_bull": True, "extra_guess": True},
                          player2_id: {"reveal_bull": True, "extra_guess": True}}
        self.spectators = set()  # user_ids
        self.live_feed = []  # (user_id, guess, bulls, cows)

    def set_code(self, user_id, code):
        if self._is_valid_code(code):
            self.codes[user_id] = code
            return True
        return False

    def ready(self):
        return len(self.codes) == 2

    def make_guess(self, user_id, guess):
        if not self.ready() or self.ended:
            return {"error": "Game not ready or already ended."}
        if user_id != self.turn:
            return {"error": "Not your turn."}
        if not self._is_valid_code(guess):
            return {"error": "Invalid guess. Use 4 unique digits."}
        opponent_id = self.player2_id if user_id == self.player1_id else self.player1_id
        code = self.codes[opponent_id]
        bulls, cows = self._score_guess(guess, code)
        self.guesses[user_id].append((guess, bulls, cows))
        self.live_feed.append((user_id, guess, bulls, cows))
        self.turn_count += 1
        result = {"bulls": bulls, "cows": cows, "win": False}
        if bulls == 4:
            self.ended = True
            self.winner = user_id
            self.xp[user_id] += 10
            self.wins[user_id] += 1
            # Streak bonus
            self.streaks[user_id] += 1
            self.streaks[opponent_id] = 0
            if self.streaks[user_id] > 1:
                bonus = 5 * (self.streaks[user_id] - 1)
                self.xp[user_id] += bonus
                result["streak_bonus"] = bonus
            result["win"] = True
        elif self.turn_count >= self.max_turns:
            self.ended = True
            self.winner = None
            self.streaks[self.player1_id] = 0
            self.streaks[self.player2_id] = 0
        self.turn = opponent_id
        return result

    def use_power_up(self, user_id, power_up):
        """Use a power-up if available. 'reveal_bull' reveals a correct digit in place, 'extra_guess' grants an extra turn."""
        if not self.power_ups[user_id].get(power_up, False):
            return {"error": "Power-up already used or invalid."}
        opponent_id = self.get_opponent(user_id)
        if power_up == "reveal_bull":
            # Reveal a bull (correct digit in correct place)
            code = self.codes.get(opponent_id)
            if not code:
                return {"error": "Opponent's code not set yet."}
            # Find a bull position (if any from previous guesses), else random
            revealed = None
            for guess, bulls, _ in self.guesses[user_id]:
                for i, (g, c) in enumerate(zip(guess, code)):
                    if g == c:
                        revealed = (i, c)
                        break
                if revealed:
                    break
            if not revealed:
                i = random.randint(0, 3)
                revealed = (i, code[i])
            self.power_ups[user_id][power_up] = False
            return {"reveal_bull": revealed}
        elif power_up == "extra_guess":
            self.power_ups[user_id][power_up] = False
            # Player gets another turn (do not switch turn)
            return {"extra_guess": True}
        return {"error": "Unknown power-up."}

    def add_spectator(self, user_id):
        """Add a spectator to the session."""
        self.spectators.add(user_id)

    def remove_spectator(self, user_id):
        """Remove a spectator from the session."""
        self.spectators.discard(user_id)

    def get_live_feed(self):
        """Return the live feed of guesses/results for spectators."""
        return list(self.live_feed)

    def get_state_json(self):
        return json.dumps({
            "xp": self.xp,
            "wins": self.wins,
            "guesses": self.guesses,
            "turn": self.turn,
            "ended": self.ended,
            "winner": self.winner
        })

    def load_state_json(self, state_json):
        state = json.loads(state_json)
        self.xp = state["xp"]
        self.wins = state["wins"]
        self.guesses = state["guesses"]
        self.turn = state["turn"]
        self.ended = state["ended"]
        self.winner = state["winner"]

    def _is_valid_code(self, code):
        return len(code) == 4 and code.isdigit() and len(set(code)) == 4

    def _score_guess(self, guess, code):
        bulls = sum(a == b for a, b in zip(guess, code))
        cows = sum(min(guess.count(d), code.count(d)) for d in set(guess)) - bulls
        return bulls, cows

    def get_opponent(self, user_id):
        return self.player2_id if user_id == self.player1_id else self.player1_id

    def is_ended(self):
        return self.ended

    def get_winner(self):
        return self.winner

    def get_xp(self, user_id):
        return self.xp.get(user_id, 0)

    def get_wins(self, user_id):
        return self.wins.get(user_id, 0)

    def get_turn(self):
        return self.turn

    def get_codes_set(self):
        return list(self.codes.keys())

    def rematch(self):
        """Reset the session for a rematch, keeping XP and win counts."""
        self.codes = {}
        self.guesses = {self.player1_id: [], self.player2_id: []}
        self.turn = self.player1_id
        self.ended = False
        self.winner = None
        self.turn_count = 0

    def get_stats(self):
        """Return stats summary for both players."""
        return {
            str(self.player1_id): {
                "xp": self.xp[self.player1_id],
                "wins": self.wins[self.player1_id],
                "guesses": len(self.guesses[self.player1_id])
            },
            str(self.player2_id): {
                "xp": self.xp[self.player2_id],
                "wins": self.wins[self.player2_id],
                "guesses": len(self.guesses[self.player2_id])
            },
            "games_played": self.wins[self.player1_id] + self.wins[self.player2_id]
        }
 