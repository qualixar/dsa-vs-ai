"""Input generator for merge-k-sorted-lists. `generate` makes small inputs for the slow machine; `big` makes one large input for fast, and `big_check` tests the answer to it."""
from checking import strict_equal
from structures import linked, values_of

TITLE = "Merge k Sorted Lists"
FAMILY = "Heaps"
LEETCODE = (23, "merge-k-sorted-lists")

MAX_SIZE = 5


def generate(rng, size):
    lists = []
    for _ in range(rng.randint(0, size + 1)):
        lists.append(linked(sorted(rng.randint(0, 9) for _ in range(rng.randint(0, 3)))))
    return (lists,)


def edges():
    return [([linked([-2**31, 2**31 - 1]), linked([0])],), ([linked([2**31 - 1]), None, linked([-2**31])],)]


def big(rng):
    return ([linked(sorted(rng.randint(0, 10**6) for _ in range(500))) for _ in range(400)],)


def big_check(args, got):
    everything = []
    for head in args[0]:
        everything += values_of(head)
    return strict_equal(values_of(got), sorted(everything))


def same(args, got, want):
    return strict_equal(values_of(got), values_of(want))
