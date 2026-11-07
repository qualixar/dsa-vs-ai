"""Input generator for search-in-rotated-sorted-array. `generate` makes small inputs for the slow machine; `big` makes one large input for fast, and `big_check` tests the answer to it."""
from checking import strict_equal

TITLE = "Search in Rotated Sorted Array"
FAMILY = "Binary search"
LEETCODE = (33, "search-in-rotated-sorted-array")

MAX_SIZE = 9


def generate(rng, size):
    values = sorted(rng.sample(range(0, 15), size + 1))
    cut = rng.randrange(len(values))
    return (values[cut:] + values[:cut], rng.randint(-1, 15))


def edges():
    return [([2**31 - 1, -2**31], -2**31), ([-2**31], 2**31 - 1), ([0, 2**31 - 1, -2**31], 2**31 - 1)]


def big(rng):
    values = list(range(300000))
    return (values[100000:] + values[:100000], 7)


def big_check(args, got):
    """The value 7 sits 7 places after the wrap point, which is known from how the list was cut."""
    return strict_equal(got, 200007)
