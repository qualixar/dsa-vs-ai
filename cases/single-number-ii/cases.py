"""Input generator for single-number-ii. `generate` makes small inputs for the slow machine; `big` makes one large input for fast, and `big_check` tests the answer to it."""
from checking import strict_equal
from collections import Counter

TITLE = "Single Number II"
FAMILY = "Bit tricks"
LEETCODE = (137, "single-number-ii")

MAX_SIZE = 5


def generate(rng, size):
    pool = range(-2**31, 2**31) if rng.random() < 0.5 else range(-20, 21)
    values = rng.sample(pool, size + 1)
    nums = [values[0]] + [v for v in values[1:] for _ in range(3)]
    rng.shuffle(nums)
    return (nums,)


def edges():
    """Each end of the 32-bit range, as the single value and as a tripled one."""
    return [([-2**31],), ([2**31 - 1],), ([5, 5, 5, -2**31],), ([5, 5, 5, 2**31 - 1],),
            ([2**31 - 1] * 3 + [-2**31],), ([-2**31] * 3 + [2**31 - 1],), ([-1, -1, -1, 2**16],), ([2**16] * 3 + [-1],)]


def big(rng):
    values = rng.sample(range(-2**31, 2**31 - 1), 20001)
    nums = [values[0]] + [v for v in values[1:] for _ in range(3)]
    rng.shuffle(nums)
    return (nums,)


def big_check(args, got):
    """Count each value."""
    singles = [v for v, n in Counter(args[0]).items() if n == 1]
    return strict_equal(got, singles[0])
