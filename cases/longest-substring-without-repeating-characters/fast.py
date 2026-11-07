def solve(s):
    last = {}
    start = best = 0
    for i, c in enumerate(s):
        if c in last:
            start = max(start, last[c] + 1)
        last[c] = i
        best = max(best, i - start + 1)
    return best
