from collections import defaultdict
from heapq import heappop, heappush


def solve(times, n, k):
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
                heappush(heap, (d + w, v))
    return max(dist.values()) if len(dist) == n else -1
