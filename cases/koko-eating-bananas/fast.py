def solve(piles, h):
    lo, hi = 1, max(piles)
    while lo < hi:
        speed = (lo + hi) // 2
        hours = sum((p + speed - 1) // speed for p in piles)
        if hours <= h:
            hi = speed
        else:
            lo = speed + 1
    return lo
