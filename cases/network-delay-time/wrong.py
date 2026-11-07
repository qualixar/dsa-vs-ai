"""Two wrong answers to hunt. Run the check first; README.md explains both behind a fold."""
from collections import defaultdict, deque
from heapq import heappop, heappush


def gut(times, n, k):
    """Breadth-first search: the route with the fewest hops gives each node's time."""
    graph = defaultdict(list)
    for u, v, w in times:
        graph[u].append((v, w))
    dist = {k: 0}
    queue = deque([k])
    while queue:
        u = queue.popleft()
        for v, w in graph[u]:
            if v not in dist:
                dist[v] = dist[u] + w
                queue.append(v)
    return max(dist.values()) if len(dist) == n else -1


# A copy of fast.py with exactly one line changed. Find it.
def planted(times, n, k):
    graph = defaultdict(list)
    for u, v, w in times:
        graph[u].append((v, w))
    dist = {}
    heap = [(0, k)]
    while heap:
        d, u = heappop(heap)
        if u in dist:
            continue
        dist[u] = d
        for v, w in graph[u]:
            if v not in dist:
                heappush(heap, (w, v))
    return max(dist.values()) if len(dist) == n else -1
