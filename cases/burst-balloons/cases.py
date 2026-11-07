"""Input generator for burst-balloons. `generate` makes small inputs for the slow machine; `big` makes one large input for fast, and `big_check` tests the answer to it."""
from checking import strict_equal

TITLE = "Burst Balloons"
FAMILY = "DP: intervals"
LEETCODE = (312, "burst-balloons")

MAX_SIZE = 6


def generate(rng, size):
    return ([rng.randint(0, 6) for _ in range(size + 1)],)


def big(rng):
    return ([rng.randint(0, 100) for _ in range(120)],)


def big_check(args, got):
    """The same recurrence, written top down with a memo, so a slip in the loop order of fast.py would show."""
    vals = [1] + args[0] + [1]
    memo = {}
    def best(left, right):
        if right - left < 2:
            return 0
        key = (left, right)
        if key not in memo:
            memo[key] = max(vals[left] * vals[m] * vals[right] + best(left, m) + best(m, right) for m in range(left + 1, right))
        return memo[key]
    return strict_equal(got, best(0, len(vals) - 1))
