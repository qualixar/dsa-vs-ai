"""Input generator for container-with-most-water. `generate` makes small inputs for the slow machine; `big` makes one large input for fast, and `big_check` tests the answer to it."""
from checking import strict_equal

TITLE = "Container With Most Water"
FAMILY = "Two pointers"
LEETCODE = (11, "container-with-most-water")

MAX_SIZE = 9


def generate(rng, size):
    return ([rng.randint(0, 9) for _ in range(size + 2)],)


def edges():
    return [([2**31 - 1, 2**31 - 1],), ([0, 2**31 - 1, 2**31 - 1, 0],)]


def big(rng):
    inner = [rng.randint(0, 10**5) for _ in range(200000)]
    return ([10**5 + 1] + inner + [10**5 + 1],)


def big_check(args, got):
    """The two ends are at least as tall as anything inside and as far apart as possible, so they are the best pair."""
    return strict_equal(got, (len(args[0]) - 1) * (10**5 + 1))
