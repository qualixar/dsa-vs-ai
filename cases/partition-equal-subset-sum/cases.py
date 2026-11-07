"""Input generator for partition-equal-subset-sum. `generate` makes small inputs for the slow machine; `big` makes one large input for fast, and `big_check` tests the answer to it."""
from checking import strict_equal

TITLE = "Partition Equal Subset Sum"
FAMILY = "DP: 2D"
LEETCODE = (416, "partition-equal-subset-sum")

MAX_SIZE = 9


def generate(rng, size):
    return ([rng.randint(1, 9) for _ in range(size + 1)],)


def big(rng):
    return ([rng.randint(1, 100) for _ in range(400)],)


def big_check(args, got):
    """Reachable sums held in the bits of one big integer, instead of a table."""
    reach = 1
    for x in args[0]:
        reach |= reach << x
    total = sum(args[0])
    return strict_equal(got, total % 2 == 0 and bool(reach >> (total // 2) & 1))
