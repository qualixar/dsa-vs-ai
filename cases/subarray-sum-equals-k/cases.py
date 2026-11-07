"""Input generator for subarray-sum-equals-k. `generate` makes small inputs for the slow machine; `big` makes one large input for fast, and `big_check` tests the answer to it."""
from checking import strict_equal

TITLE = "Subarray Sum Equals K"
FAMILY = "Arrays and hashing"
LEETCODE = (560, "subarray-sum-equals-k")

MAX_SIZE = 9


def generate(rng, size):
    return ([rng.randint(-3, 3) for _ in range(size)], rng.randint(-4, 4))


def edges():
    return [([2**31 - 1, -2**31, 1], 0), ([2**31 - 1], 2**31 - 1), ([-2**31], -2**31)]


def big(rng):
    return ([1, -1] * 100000, 0)


def big_check(args, got):
    """Running totals alternate 0, 1, 0, 1, so a zero-sum stretch is any pair of equal running totals."""
    half = len(args[0]) // 2
    zeros, ones = half + 1, half
    return strict_equal(got, zeros * (zeros - 1) // 2 + ones * (ones - 1) // 2)
