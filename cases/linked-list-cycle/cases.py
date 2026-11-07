"""Input generator for linked-list-cycle. `generate` makes small inputs for the slow machine; `big` makes one large input for fast, and `big_check` tests the answer to it."""
from checking import strict_equal
from structures import linked

TITLE = "Linked List Cycle"
FAMILY = "Linked structures"
LEETCODE = (141, "linked-list-cycle")

MAX_SIZE = 8


def generate(rng, size):
    values = [rng.randint(0, 3) for _ in range(size)]
    loop_to = rng.randrange(size) if size and rng.random() < 0.5 else None
    return (linked(values, loop_to),)


def big(rng):
    return (linked(list(range(300000)), 150000),)


def big_check(args, got):
    """The list loops by construction."""
    return strict_equal(got, True)
