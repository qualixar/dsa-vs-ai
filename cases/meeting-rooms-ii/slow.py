def solve(meetings):
    """At each start time, count the meetings under way."""
    best = 0
    for start, _ in meetings:
        best = max(best, sum(1 for a, b in meetings if a <= start < b))
    return best
