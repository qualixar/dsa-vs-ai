from math import inf


def solve(n, flights, src, dst, k):
    cost = [inf] * n
    cost[src] = 0
    for _ in range(k + 1):
        before = cost[:]
        for a, b, price in flights:
            if before[a] + price < cost[b]:
                cost[b] = before[a] + price
    return cost[dst] if cost[dst] < inf else -1
