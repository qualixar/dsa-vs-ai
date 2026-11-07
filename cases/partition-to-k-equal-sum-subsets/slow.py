from itertools import product


def solve(nums, k):
    """Try every way of assigning numbers to groups."""
    for groups in product(range(k), repeat=len(nums)):
        totals = [0] * k
        for x, g in zip(nums, groups):
            totals[g] += x
        if len(set(totals)) == 1:
            return True
    return False
