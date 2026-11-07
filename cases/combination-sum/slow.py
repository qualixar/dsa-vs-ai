from itertools import product


def solve(candidates, target):
    """Try every count of every candidate."""
    ranges = [range(target // c + 1) for c in candidates]
    out = []
    for counts in product(*ranges):
        if sum(n * c for n, c in zip(counts, candidates)) == target:
            out.append([c for n, c in zip(counts, candidates) for _ in range(n)])
    return out
