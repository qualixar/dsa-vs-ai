"""Input generator for longest-substring-without-repeating-characters. `generate` makes small inputs for the slow machine; `big` makes one large input for fast, and `big_check` tests the answer to it."""
from checking import strict_equal

TITLE = "Longest Substring Without Repeating Characters"
FAMILY = "Sliding window"
LEETCODE = (3, "longest-substring-without-repeating-characters")

MAX_SIZE = 9


def generate(rng, size):
    return ("".join(rng.choice("abcd") for _ in range(size)),)


def big(rng):
    return ("".join(rng.choice("abcdefghijklmnopqrstuvwxyz") for _ in range(100000)),)


def big_check(args, got):
    """No run can pass 26 letters, so testing up to 26 letters from each start is exact."""
    s = args[0]
    best = 0
    for i in range(len(s)):
        seen = set()
        for c in s[i:i + 27]:
            if c in seen:
                break
            seen.add(c)
        best = max(best, len(seen))
    return strict_equal(got, best)
