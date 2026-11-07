"""Input generator for koko-eating-bananas. `generate` makes small inputs for the slow machine; `big` makes one large input for fast, and `big_check` tests the answer to it."""

TITLE = "Koko Eating Bananas"
FAMILY = "Binary search"
LEETCODE = (875, "koko-eating-bananas")

MAX_SIZE = 6


def generate(rng, size):
    piles = [rng.randint(1, 12) for _ in range(size + 1)]
    return (piles, len(piles) + rng.randint(0, 6))


def big(rng):
    return ([rng.randint(1, 10**9) for _ in range(100000)], 200000)


def big_check(args, got):
    """By definition: this speed finishes in time and one speed slower does not."""
    piles, h = args
    if type(got) is not int or got < 1:
        return False
    hours = lambda speed: sum((p + speed - 1) // speed for p in piles)
    return hours(got) <= h and (got == 1 or hours(got - 1) > h)
