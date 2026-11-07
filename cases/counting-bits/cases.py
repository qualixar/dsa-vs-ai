"""Input generator for counting-bits. `generate` makes small inputs for the slow machine; `big` makes one large input for fast, and `big_check` tests the answer to it."""
from checking import strict_equal

TITLE = "Counting Bits"
FAMILY = "Bit tricks"
LEETCODE = (338, "counting-bits")

MAX_SIZE = 200


def generate(rng, size):
    return (size,)


def big(rng):
    return (300000,)


def big_check(args, got):
    return strict_equal(got, [bin(i).count("1") for i in range(args[0] + 1)])
