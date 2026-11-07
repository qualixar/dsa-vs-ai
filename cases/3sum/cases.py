"""Input generator for 3sum. `generate` makes small inputs for the slow machine; `big` makes one large input for fast, and `big_check` tests the answer to it."""
from checking import is_groups
from collections import Counter

TITLE = "3Sum"
FAMILY = "Two pointers"
LEETCODE = (15, "3sum")

MAX_SIZE = 8


def generate(rng, size):
    return ([rng.randint(-4, 4) for _ in range(size)],)


def edges():
    return [([2**31 - 1, -2**31, 1],), ([-2**31, 2**31 - 1, 1, 0],)]


def big(rng):
    return ([rng.randint(-300, 300) for _ in range(3000)],)


def big_check(args, got):
    """Walk the distinct values by count, a different route from sorting and closing in."""
    counts = Counter(args[0])
    values = sorted(counts)
    want = []
    for i, a in enumerate(values):
        for b in values[i:]:
            c = -a - b
            if c < b or c not in counts:
                continue
            need = Counter((a, b, c))
            if all(counts[v] >= n for v, n in need.items()):
                want.append([a, b, c])
    return same(args, got, want)


def same(args, got, want):
    """Order does not matter, but a repeated triple does, and each triple must be three whole numbers."""
    return is_groups(got, 3) and sorted(sorted(t) for t in got) == sorted(sorted(t) for t in want)
