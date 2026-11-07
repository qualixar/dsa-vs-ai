def solve(piles, h):
    """Try every speed from 1 up."""
    speed = 1
    while sum((p + speed - 1) // speed for p in piles) > h:
        speed += 1
    return speed
