from math import inf


def solve(intervals):
    kept = 0
    last_end = -inf
    for start, end in sorted(intervals, key=lambda it: it[1]):
        if start >= last_end:
            kept += 1
            last_end = end
    return len(intervals) - kept
