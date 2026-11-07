from itertools import combinations


def solve(intervals):
    """Try keeping every subset, largest first."""
    for keep in range(len(intervals), -1, -1):
        for chosen in combinations(intervals, keep):
            ordered = sorted(chosen)
            if all(a[1] <= b[0] for a, b in zip(ordered, ordered[1:])):
                return len(intervals) - keep
