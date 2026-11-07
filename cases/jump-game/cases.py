"""Input generator for jump-game. `generate` makes small inputs for the slow machine; `big` makes one large input for fast, and `big_check` tests the answer to it."""
from checking import strict_equal

TITLE = "Jump Game"
FAMILY = "Greedy"
LEETCODE = (55, "jump-game")

MAX_SIZE = 10


def generate(rng, size):
    return ([rng.randint(0, 3) for _ in range(size + 1)],)


def big(rng):
    return ([rng.randint(1, 3) for _ in range(300000)],)


def big_check(args, got):
    """No zeros, so every position can always move forward: the answer is yes."""
    return strict_equal(got, True)
