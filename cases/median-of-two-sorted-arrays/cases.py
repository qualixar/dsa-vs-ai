"""Input generator for median-of-two-sorted-arrays. `generate` makes small inputs for the slow machine; `big` makes one large input for fast, and `big_check` tests the answer to it."""

TITLE = "Median of Two Sorted Arrays"
FAMILY = "Binary search"
LEETCODE = (4, "median-of-two-sorted-arrays")

MAX_SIZE = 9


def generate(rng, size):
    a_size = rng.randint(0, size + 1)
    b_size = size + 1 - a_size
    a = sorted(rng.randint(-9, 9) for _ in range(a_size))
    b = sorted(rng.randint(-9, 9) for _ in range(b_size))
    return (a, b)


def edges():
    return [([-2**31], [2**31 - 1]), ([2**31 - 1], [2**31 - 1]), ([-2**31], [-2**31, 2**31 - 1])]


def big(rng):
    return (sorted(rng.randint(0, 10**9) for _ in range(200000)), sorted(rng.randint(0, 10**9) for _ in range(200000)))


def big_check(args, got):
    merged = sorted(args[0] + args[1])
    n = len(merged)
    want = float(merged[n // 2]) if n % 2 else (merged[n // 2 - 1] + merged[n // 2]) / 2
    return same(args, got, want)


def same(args, got, want):
    """A whole number or a float is fine, and a bool or text is not. The two must match to within rounding."""
    return type(got) in (int, float) and abs(got - want) <= 1e-9
