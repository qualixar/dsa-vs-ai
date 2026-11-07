"""Input generator for combination-sum. `generate` makes small inputs for the slow machine; `big` makes one large input for fast, and `big_check` tests the answer to it."""
from checking import is_groups

TITLE = "Combination Sum"
FAMILY = "Backtracking"
LEETCODE = (39, "combination-sum")

MAX_SIZE = 5


def generate(rng, size):
    candidates = rng.sample(range(1, 10), size + 1)
    return (candidates, rng.randint(1, 12))


def big(rng):
    return ([3, 5, 7, 11, 13, 17], 150)


def big_check(args, got):
    """Count the combinations with a table, then test each one returned: right numbers, right sum, none repeated."""
    candidates, target = args
    ways = [1] + [0] * target
    for c in candidates:
        for s in range(c, target + 1):
            ways[s] += ways[s - c]
    if not is_groups(got) or len(got) != ways[target]:
        return False
    seen = {tuple(sorted(c)) for c in got}
    return len(seen) == len(got) and all(sum(c) == target and set(c) <= set(candidates) for c in got)


def same(args, got, want):
    """Order does not matter, but a repeated combination does, and each must hold only whole numbers."""
    return is_groups(got) and sorted(sorted(c) for c in got) == sorted(sorted(c) for c in want)
