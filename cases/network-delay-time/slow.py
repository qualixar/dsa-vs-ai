def solve(times, n, k):
    """Relax every edge, n times over."""
    dist = {i: float("inf") for i in range(1, n + 1)}
    dist[k] = 0
    for _ in range(n):
        for u, v, w in times:
            dist[v] = min(dist[v], dist[u] + w)
    worst = max(dist.values())
    return -1 if worst == float("inf") else worst
