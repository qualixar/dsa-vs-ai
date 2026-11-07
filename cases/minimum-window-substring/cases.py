"""Input generator for minimum-window-substring. `generate` makes small inputs for the slow machine; `big` makes one large input for fast, and `big_check` tests the answer to it."""
from collections import Counter

TITLE = "Minimum Window Substring"
FAMILY = "Sliding window"
LEETCODE = (76, "minimum-window-substring")

MAX_SIZE = 9


def generate(rng, size):
    s = "".join(rng.choice("abc") for _ in range(size + 1))
    t = "".join(rng.choice("abc") for _ in range(rng.randint(1, 3)))
    return (s, t)


def big(rng):
    noise = "".join(rng.choice("abcdefg") for _ in range(200000))
    return (noise[:50000] + "x" + noise[50000:90000] + "y" + noise[90000:120000] + "z" + noise[120000:], "xyz")


def big_check(args, got):
    """x, y and z each appear once, so the only window runs from x to z."""
    s = args[0]
    return same(args, got, s[s.index("x"):s.index("z") + 1])


def same(args, got, want):
    """Several windows can tie, so test that it is text, its length, that it comes from s and that it covers t."""
    s, t = args
    if type(got) is not str or len(got) != len(want) or got not in s:
        return False
    return not want or not Counter(t) - Counter(got)
