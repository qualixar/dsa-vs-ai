def solve(n, flights, src, dst, k):
    """Walk every route with few enough flights."""
    best = -1
    def walk(place, used, cost):
        nonlocal best
        if place == dst:
            best = cost if best < 0 else min(best, cost)
            return
        if used == k + 1:
            return
        for a, b, price in flights:
            if a == place:
                walk(b, used + 1, cost + price)
    walk(src, 0, 0)
    return best
