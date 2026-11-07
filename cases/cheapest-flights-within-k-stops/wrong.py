"""Two wrong answers to hunt. Run the check first; README.md explains both behind a fold."""
from heapq import heappop, heappush
from math import inf


def gut(n, flights, src, dst, k):
    """Dijkstra's algorithm with a stop limit and a visited set."""
    links = {}
    for a, b, price in flights:
        links.setdefault(a, []).append((b, price))
    done = set()
    heap = [(0, src, 0)]
    while heap:
        cost, place, used = heappop(heap)
        if place == dst:
            return cost
        if place in done or used > k:
            continue
        done.add(place)
        for b, price in links.get(place, []):
            heappush(heap, (cost + price, b, used + 1))
    return -1


# A copy of fast.py with exactly one line changed. Find it.
def planted(n, flights, src, dst, k):
    cost = [inf] * n
    cost[src] = 0
    for _ in range(k + 1):
        before = cost
        for a, b, price in flights:
            if before[a] + price < cost[b]:
                cost[b] = before[a] + price
    return cost[dst] if cost[dst] < inf else -1
