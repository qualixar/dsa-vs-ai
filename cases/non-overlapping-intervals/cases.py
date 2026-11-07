"""Input generator for non-overlapping-intervals. `generate` makes small inputs for the slow machine; `big` makes one large input for fast, and `big_check` tests the answer to it."""
from bisect import bisect_right
from checking import strict_equal

TITLE = "Non-overlapping Intervals"
FAMILY = "Greedy"
LEETCODE = (435, "non-overlapping-intervals")

MAX_SIZE = 8


def generate(rng, size):
    out = []
    for _ in range(size):
        start = rng.randint(0, 10)
        out.append([start, start + rng.randint(1, 5)])
    return (out,)


def edges():
    return [([[-5, -3], [-4, -2]],), ([[-2**31, 2**31 - 1], [0, 1]],), ([[-5, -3], [-3, -1]],)]


def big(rng):
    out = []
    for _ in range(100000):
        start = rng.randint(0, 10**7)
        out.append([start, start + rng.randint(1, 100)])
    return (out,)


def big_check(args, got):
    """A table of the most intervals keepable, sorted by end, with no greedy choice."""
    items = sorted(args[0], key=lambda it: it[1])
    ends = [b for _, b in items]
    keep = [0] * (len(items) + 1)
    for i, (a, _) in enumerate(items):
        keep[i + 1] = max(keep[i], keep[bisect_right(ends, a, 0, i)] + 1)
    return strict_equal(got, len(items) - keep[-1])
