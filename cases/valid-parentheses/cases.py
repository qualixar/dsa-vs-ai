"""Input generator for valid-parentheses. `generate` makes small inputs for the slow machine; `big` makes one large input for fast, and `big_check` tests the answer to it."""
from checking import strict_equal

TITLE = "Valid Parentheses"
FAMILY = "Stacks"
LEETCODE = (20, "valid-parentheses")

MAX_SIZE = 10


def generate(rng, size):
    if rng.random() < 0.5:
        return ("".join(rng.choice("()[]{}") for _ in range(size)),)
    out = ""
    for _ in range(size // 2):
        pair = rng.choice(("()", "[]", "{}"))
        where = rng.randint(0, len(out))
        out = out[:where] + pair + out[where:]
    return (out,)


def big(rng):
    return ("([{" * 50000 + "}])" * 50000,)


def big_check(args, got):
    """Nested by construction, so the answer is yes."""
    return strict_equal(got, True)
