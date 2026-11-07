"""Input generator for product-of-array-except-self. `generate` makes small inputs for the slow machine; `big` makes one large input for fast, and `big_check` tests the answer to it."""
from checking import strict_equal

TITLE = "Product of Array Except Self"
FAMILY = "Arrays and hashing"
LEETCODE = (238, "product-of-array-except-self")

MAX_SIZE = 7


def generate(rng, size):
    return ([rng.randint(-3, 3) for _ in range(size + 1)],)


def edges():
    return [([2**31 - 1, 1],), ([-2**31, 1],), ([-1, -2**31],)]


def big(rng):
    return ([rng.choice((-1, 1)) for _ in range(200000)],)


def big_check(args, got):
    """Every entry is 1 or -1, so dividing the total by an entry is the same as multiplying by it."""
    total = 1
    for x in args[0]:
        total *= x
    return strict_equal(got, [total * x for x in args[0]])
