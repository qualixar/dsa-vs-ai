"""Input generator for word-search. `generate` makes small inputs for the slow machine; `big` makes one large input for fast, and `big_check` tests the answer to it."""
from checking import strict_equal

TITLE = "Word Search"
FAMILY = "Backtracking"
LEETCODE = (79, "word-search")

MAX_SIZE = 5


def generate(rng, size):
    rows, cols = rng.randint(1, 3), rng.randint(1, 3)
    board = [[rng.choice("ab") for _ in range(cols)] for _ in range(rows)]
    word = "".join(rng.choice("ab") for _ in range(size + 1))
    return (board, word)


def big(rng):
    return ([["a"] * 5 for _ in range(5)], "aaaaaaaab")


def big_check(args, got):
    """The board has no b, so the answer is no."""
    return strict_equal(got, False)
