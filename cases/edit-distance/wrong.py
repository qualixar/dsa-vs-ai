"""Two wrong answers to hunt. Run the check first; README.md explains both behind a fold."""


def gut(a, b):
    """Count the positions that differ, plus the difference in length."""
    return sum(x != y for x, y in zip(a, b)) + abs(len(a) - len(b))


# A copy of fast.py with exactly one line changed. Find it.
def planted(a, b):
    row = list(range(len(b) + 1))
    for i, x in enumerate(a, 1):
        prev, row[0] = row[0], i
        for j, y in enumerate(b, 1):
            cost = 0 if x == y else 2
            prev, row[j] = row[j], min(row[j] + 1, row[j - 1] + 1, prev + cost)
    return row[-1]
