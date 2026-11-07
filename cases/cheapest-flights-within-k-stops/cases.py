"""Input generator for cheapest-flights-within-k-stops. `generate` makes small inputs for the slow machine; `big` makes one large input for fast, and `big_check` tests the answer to it."""
from checking import strict_equal
from heapq import heappop, heappush

TITLE = "Cheapest Flights Within K Stops"
FAMILY = "Graphs"
LEETCODE = (787, "cheapest-flights-within-k-stops")

MAX_SIZE = 8


def generate(rng, size):
    """Some inputs hold a cheap route that uses up the stop budget, because random graphs rarely make one."""
    if rng.random() < 0.3:
        a, b, c, d, e = rng.sample(range(6), 5)
        flights = [[a, b, rng.randint(1, 2)], [b, c, rng.randint(1, 2)], [a, c, rng.randint(4, 8)], [c, d, 1], [d, e, 1]]
        rng.shuffle(flights)
        return (6, flights, a, e, 2)
    n = size // 2 + 3
    flights = {}
    for _ in range(size + 2):
        a, b = rng.sample(range(n), 2)
        flights[(a, b)] = rng.randint(1, 9)
    src, dst = rng.sample(range(n), 2)
    return (n, [[a, b, p] for (a, b), p in flights.items()], src, dst, rng.randint(0, 3))


def edges():
    return [(2, [[0, 1, 2**31 - 1]], 0, 1, 0), (3, [[0, 1, 2**31 - 1], [1, 2, 2**31 - 1]], 0, 2, 1)]


def big(rng):
    n = 2000
    flights = [[rng.randrange(n), rng.randrange(n), rng.randint(1, 100)] for _ in range(20000)]
    return (n, flights, 0, n - 1, 20)


def big_check(args, got):
    """Dijkstra's algorithm over (city, flights used) pairs, not rounds of relaxation."""
    n, flights, src, dst, k = args
    links = {}
    for a, b, price in flights:
        links.setdefault(a, []).append((b, price))
    done = set()
    heap = [(0, src, 0)]
    want = -1
    while heap:
        cost, place, used = heappop(heap)
        if place == dst:
            want = cost
            break
        if (place, used) in done or used > k:
            continue
        done.add((place, used))
        for b, price in links.get(place, []):
            heappush(heap, (cost + price, b, used + 1))
    return strict_equal(got, want)
