"""Pure-Python rules for the number guessing game (no Django imports, easy to test)."""

import secrets

MIN_NUMBER = 1
MAX_NUMBER = 100
MAX_ATTEMPTS = 7


def new_secret():
    """Pick the secret number using a cryptographically strong RNG."""
    return MIN_NUMBER + secrets.randbelow(MAX_NUMBER - MIN_NUMBER + 1)


def check_guess(secret, guess):
    """Return 'correct', 'higher' (secret is higher) or 'lower' (secret is lower)."""
    if guess == secret:
        return "correct"
    return "higher" if guess < secret else "lower"


def points_for_win(attempts_used):
    """Fewer attempts means more points: 7 attempts -> 10 pts ... 1 attempt -> 70 pts."""
    return max(0, (MAX_ATTEMPTS - attempts_used + 1) * 10)
