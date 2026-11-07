"""Input generator for reverse-nodes-in-k-group. `generate` makes small inputs for the slow machine; `big` makes one large input for fast, and `big_check` tests the answer to it."""
from checking import strict_equal
from structures import linked, values_of

TITLE = "Reverse Nodes in k-Group"
FAMILY = "Linked structures"
LEETCODE = (25, "reverse-nodes-in-k-group")

MAX_SIZE = 9


def generate(rng, size):
    return (linked([rng.randint(0, 9) for _ in range(size)]), rng.randint(1, 4))


def edges():
    return [(linked([-2**31, 2**31 - 1]), 2)]


def big(rng):
    return (linked(list(range(300000))), 7)


def big_check(args, got):
    values = values_of(args[0])
    want = []
    for i in range(0, len(values), 7):
        block = values[i:i + 7]
        want += block[::-1] if len(block) == 7 else block
    return strict_equal(values_of(got), want)


def same(args, got, want):
    return strict_equal(values_of(got), values_of(want))
