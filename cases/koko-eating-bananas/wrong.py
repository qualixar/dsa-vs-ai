"""Two wrong answers to hunt. Run the check first; README.md explains both behind a fold."""


def gut(piles, h):
    """Average: total food divided by total hours, rounded up."""
    return (sum(piles) + h - 1) // h


# A copy of fast.py with exactly one line changed. Find it.
def planted(piles, h):
    lo, hi = 1, max(piles)
    while lo < hi:
        speed = (lo + hi) // 2
        hours = sum(p // speed + 1 for p in piles)
        if hours <= h:
            hi = speed
        else:
            lo = speed + 1
    return lo
