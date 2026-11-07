"""Two wrong answers to hunt. Run the check first; README.md explains both behind a fold."""
from math import inf


def gut(intervals):
    """Sort by start time and keep whatever starts first."""
    kept = 0
    last_end = -inf
    for start, end in sorted(intervals):
        if start >= last_end:
            kept += 1
            last_end = end
    return len(intervals) - kept


# A copy of fast.py with exactly one line changed. Find it.
def planted(intervals):
    kept = 0
    last_end = -inf
    for start, end in sorted(intervals, key=lambda it: it[1]):
        if start > last_end:
            kept += 1
            last_end = end
    return len(intervals) - kept
