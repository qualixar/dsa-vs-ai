"""Input generator for longest-increasing-subsequence. `generate` makes small inputs for the slow machine; `big` makes one large input for fast, and `big_check` tests the answer to it."""
from bisect import bisect_left
from checking import strict_equal

TITLE = "Longest Increasing Subsequence"
FAMILY = "DP: 1D"
LEETCODE = (300, "longest-increasing-subsequence")

MAX_SIZE = 10


def generate(rng, size):
    return ([rng.randint(0, 7) for _ in range(size)],)


def edges():
    return [([-2**31],), ([-2**31, 2**31 - 1],), ([2**31 - 1, -2**31],)]


def big(rng):
    return ([rng.randint(0, 10**9) for _ in range(100000)],)


def big_check(args, got):
    """A Fenwick tree over the ranks of the values, instead of a list of tails."""
    ranks = sorted(set(args[0]))
    tree = [0] * (len(ranks) + 1)
    best = 0
    for x in args[0]:
        i = bisect_left(ranks, x)
        length, j = 0, i
        while j > 0:
            length = max(length, tree[j])
            j -= j & -j
        length += 1
        best = max(best, length)
        j = i + 1
        while j <= len(ranks):
            tree[j] = max(tree[j], length)
            j += j & -j
    return strict_equal(got, best)
