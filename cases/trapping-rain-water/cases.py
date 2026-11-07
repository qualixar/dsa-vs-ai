"""Input generator for trapping-rain-water. `generate` makes small inputs for the slow machine; `big` makes one large input for fast, and `big_check` tests the answer to it."""
from checking import strict_equal

TITLE = "Trapping Rain Water"
FAMILY = "Two pointers"
LEETCODE = (42, "trapping-rain-water")

MAX_SIZE = 9


def generate(rng, size):
    return ([rng.randint(0, 5) for _ in range(size)],)


def edges():
    return [([2**31 - 1, 0, 2**31 - 1],), ([2**31 - 1, 2**31 - 1],)]


def big(rng):
    return ([rng.randint(0, 10**5) for _ in range(200000)],)


def big_check(args, got):
    """Tallest bar so far from each side, in two arrays, instead of two moving pointers."""
    h = args[0]
    left, right = h[:], h[:]
    for i in range(1, len(h)):
        left[i] = max(left[i - 1], h[i])
    for i in range(len(h) - 2, -1, -1):
        right[i] = max(right[i + 1], h[i])
    return strict_equal(got, sum(min(a, b) - x for a, b, x in zip(left, right, h)))
