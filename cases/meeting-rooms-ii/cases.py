"""Input generator for meeting-rooms-ii. `generate` makes small inputs for the slow machine; `big` makes one large input for fast, and `big_check` tests the answer to it."""
from checking import strict_equal

TITLE = "Meeting Rooms II"
FAMILY = "Intervals"
LEETCODE = (253, "meeting-rooms-ii")

MAX_SIZE = 7


def generate(rng, size):
    out = []
    for _ in range(size):
        start = rng.randint(0, 12)
        out.append([start, start + rng.randint(1, 6)])
    return (out,)


def edges():
    return [([[-2**31, 2**31 - 1], [0, 1]],), ([[-5, -3], [-3, -1]],), ([[-5, -3], [-4, -2]],)]


def big(rng):
    out = []
    for _ in range(100000):
        start = rng.randint(0, 10**8)
        out.append([start, start + rng.randint(1, 1000)])
    return (out,)


def big_check(args, got):
    """Count how many meetings are running, with ends before starts at a shared time, and no heap."""
    events = sorted([(a, 1) for a, _ in args[0]] + [(b, 0) for _, b in args[0]])
    depth = best = 0
    for _, kind in events:
        depth += 1 if kind else -1
        best = max(best, depth)
    return strict_equal(got, best)
