"""Input generator for word-ladder. `generate` makes small inputs for the slow machine; `big` makes one large input for fast, and `big_check` tests the answer to it."""
from checking import strict_equal
from itertools import product

TITLE = "Word Ladder"
FAMILY = "Graphs"
LEETCODE = (127, "word-ladder")

MAX_SIZE = 7
_WORDS = ["".join(p) for p in product("abc", repeat=3)]


def generate(rng, size):
    words = rng.sample(_WORDS, size + 1)
    begin = rng.choice(_WORDS)
    while begin == words[-1]:
        begin = rng.choice(_WORDS)
    end = words[-1] if rng.random() < 0.9 else rng.choice(_WORDS)
    while end == begin:
        end = rng.choice(_WORDS)
    return (begin, end, words)


def big(rng):
    words = ["".join(p) for p in product("abcdefghij", repeat=4)]
    return ("aaaa", "jjjj", words)


def big_check(args, got):
    """Every 4-letter word exists, so the chain changes each of 4 letters once: 5 words."""
    return strict_equal(got, 5)
