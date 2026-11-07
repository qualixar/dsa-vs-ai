"""Input generator for network-delay-time. `generate` makes small inputs for the slow machine; `big` makes one large input for fast, and `big_check` tests the answer to it."""
from checking import strict_equal

TITLE = "Network Delay Time"
FAMILY = "Graphs"
LEETCODE = (743, "network-delay-time")

MAX_SIZE = 7


def generate(rng, size):
    n = size // 2 + 2
    edges = {}
    for _ in range(size + 1):
        u, v = rng.sample(range(1, n + 1), 2)
        edges[(u, v)] = rng.randint(1, 9)
    return ([[u, v, w] for (u, v), w in edges.items()], n, rng.randint(1, n))


def edges():
    return [([[1, 2, 2**31 - 1]], 2, 1), ([[1, 2, 2**31 - 1], [2, 3, 2**31 - 1]], 3, 1)]


def big(rng):
    n = 50000
    edges = [[i, i + 1, rng.randint(1, 100)] for i in range(1, n)]
    edges += [[rng.randint(1, n), rng.randint(1, n), rng.randint(1, 100)] for _ in range(100000)]
    return (edges, n, 1)


def big_check(args, got):
    """Relax every edge until nothing changes, with no heap."""
    times, n, k = args
    dist = [None] * (n + 1)
    dist[k] = 0
    changed = True
    while changed:
        changed = False
        for u, v, w in times:
            if dist[u] is not None and (dist[v] is None or dist[u] + w < dist[v]):
                dist[v] = dist[u] + w
                changed = True
    return strict_equal(got, max(dist[1:]))
