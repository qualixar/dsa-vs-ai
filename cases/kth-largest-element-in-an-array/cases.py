"""Input generator for kth-largest-element-in-an-array. `generate` makes small inputs for the slow machine; `big` makes one large input for fast, and `big_check` tests the answer to it."""
from checking import strict_equal

TITLE = "Kth Largest Element in an Array"
FAMILY = "Heaps"
LEETCODE = (215, "kth-largest-element-in-an-array")

MAX_SIZE = 9


def generate(rng, size):
    nums = [rng.randint(-4, 4) for _ in range(size + 1)]
    return (nums, rng.randint(1, len(nums)))


def edges():
    return [([-2**31], 1), ([-2**31, 2**31 - 1], 2), ([2**31 - 1, 2**31 - 1], 2)]


def big(rng):
    return ([rng.randint(-10**9, 10**9) for _ in range(200000)], 1000)


def big_check(args, got):
    return strict_equal(got, sorted(args[0], reverse=True)[args[1] - 1])
