"""Input generator for largest-rectangle-in-histogram. `generate` makes small inputs for the slow machine; `big` makes one large input for fast, and `big_check` tests the answer to it."""
from checking import strict_equal

TITLE = "Largest Rectangle in Histogram"
FAMILY = "Stacks"
LEETCODE = (84, "largest-rectangle-in-histogram")

MAX_SIZE = 9


def generate(rng, size):
    return ([rng.randint(0, 6) for _ in range(size + 1)],)


def edges():
    return [([2**31 - 1],), ([2**31 - 1, 2**31 - 1],)]


def big(rng):
    return ([rng.randint(0, 10**4) for _ in range(200000)],)


def big_check(args, got):
    """Nearest shorter bar on each side, found by jumping along earlier results instead of a stack."""
    h = args[0]
    n = len(h)
    left, right = [-1] * n, [n] * n
    for i in range(n):
        j = i - 1
        while j >= 0 and h[j] >= h[i]:
            j = left[j]
        left[i] = j
    for i in range(n - 1, -1, -1):
        j = i + 1
        while j < n and h[j] >= h[i]:
            j = right[j]
        right[i] = j
    return strict_equal(got, max(h[i] * (right[i] - left[i] - 1) for i in range(n)))
