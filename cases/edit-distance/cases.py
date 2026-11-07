"""Input generator for edit-distance. `generate` makes small inputs for the slow machine; `big` makes one large input for fast, and `big_check` tests the answer to it."""
from checking import strict_equal

TITLE = "Edit Distance"
FAMILY = "DP: 2D"
LEETCODE = (72, "edit-distance")

MAX_SIZE = 5


def generate(rng, size):
    a = "".join(rng.choice("abc") for _ in range(rng.randint(0, size)))
    b = "".join(rng.choice("abc") for _ in range(rng.randint(0, size)))
    return (a, b)


def big(rng):
    letters = "abcdefgh"
    return ("".join(rng.choice(letters) for _ in range(500)), "".join(rng.choice(letters) for _ in range(500)))


def big_check(args, got):
    """The full table, top down from the ends of the strings, instead of one rolling row from the front."""
    a, b = args
    table = [[0] * (len(b) + 1) for _ in range(len(a) + 1)]
    for i in range(len(a), -1, -1):
        for j in range(len(b), -1, -1):
            if i == len(a) or j == len(b):
                table[i][j] = len(a) - i + len(b) - j
            elif a[i] == b[j]:
                table[i][j] = table[i + 1][j + 1]
            else:
                table[i][j] = 1 + min(table[i + 1][j], table[i][j + 1], table[i + 1][j + 1])
    return strict_equal(got, table[0][0])
