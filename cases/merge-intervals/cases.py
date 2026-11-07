"""Input generator for merge-intervals. `generate` makes small inputs for the slow machine; `big` makes one large input for fast, and `big_check` tests the answer to it."""
from checking import strict_equal

TITLE = "Merge Intervals"
FAMILY = "Intervals"
LEETCODE = (56, "merge-intervals")

MAX_SIZE = 6


def generate(rng, size):
    out = []
    for _ in range(size + 1):
        start = rng.randint(0, 12)
        out.append([start, start + rng.randint(0, 5)])
    return (out,)


def edges():
    return [([[-2**31, 2**31 - 1], [0, 1]],), ([[-5, -3], [-4, -2]],), ([[-2, -1], [1, 2]],)]


def big(rng):
    out = []
    for _ in range(100000):
        start = rng.randint(0, 10**8)
        out.append([start, start + rng.randint(0, 100)])
    return (out,)


def big_check(args, got):
    """Sweep over endpoints, counting how many intervals are open. Starts come first at a shared point, so touching merges."""
    events = sorted([(a, 0) for a, _ in args[0]] + [(b, 1) for _, b in args[0]])
    want = []
    depth = 0
    for point, kind in events:
        if kind == 0:
            if depth == 0:
                begin = point
            depth += 1
        else:
            depth -= 1
            if depth == 0:
                want.append([begin, point])
    return strict_equal(got, want)
