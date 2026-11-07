"""Input generator for redundant-connection. `generate` makes small inputs for the slow machine; `big` makes one large input for fast, and `big_check` tests the answer to it."""
from checking import strict_equal

TITLE = "Redundant Connection"
FAMILY = "Graphs"
LEETCODE = (684, "redundant-connection")

MAX_SIZE = 7


def generate(rng, size):
    n = size + 3
    labels = list(range(1, n + 1))
    rng.shuffle(labels)
    edges = set()
    for i in range(1, n):
        edges.add(tuple(sorted((labels[i], labels[rng.randrange(i)]))))
    while len(edges) < n:
        edges.add(tuple(sorted(rng.sample(labels, 2))))
    edges = [list(e) for e in edges]
    rng.shuffle(edges)
    return (edges,)


def big(rng):
    n = 100000
    edges = [[rng.randint(1, i - 1), i] for i in range(2, n + 1)]
    edges.append([1, n] if edges[-1][0] != 1 else [2, n])
    return (edges,)


def big_check(args, got):
    """All but the last edge form a tree, so the last edge is the one that closes the cycle."""
    return strict_equal(got, args[0][-1])
