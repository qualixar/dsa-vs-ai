"""Input generator for course-schedule-ii. `generate` makes small inputs for the slow machine; `big` makes one large input for fast, and `big_check` tests the answer to it."""
from checking import is_ints

TITLE = "Course Schedule II"
FAMILY = "Graphs"
LEETCODE = (210, "course-schedule-ii")

MAX_SIZE = 5


def generate(rng, size):
    n = size + 1
    pairs = []
    for _ in range(rng.randint(0, n + 1)):
        if n > 1:
            a, b = rng.sample(range(n), 2)
            pairs.append([a, b])
    return (n, pairs)


def big(rng):
    n = 100000
    order = list(range(n))
    rng.shuffle(order)
    return (n, [[order[i], order[i - rng.randint(1, min(i, 50))]] for i in range(1, n)])


def big_check(args, got):
    """Each pair points back along a shuffled order, so an order exists. `same` tests the order returned."""
    return same(args, got, list(range(args[0])))


def same(args, got, want):
    """Many orders can be right, so test the order itself: whole numbers, each course once, every pair respected."""
    n, pairs = args
    if not is_ints(got):
        return False
    if not want:
        return got == []
    if sorted(got) != list(range(n)):
        return False
    where = {c: i for i, c in enumerate(got)}
    return all(where[need] < where[course] for course, need in pairs)
