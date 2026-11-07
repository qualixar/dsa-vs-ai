def solve(a, b):
    """Plain recursion over the three edits, with no table."""
    if not a or not b:
        return len(a) + len(b)
    if a[0] == b[0]:
        return solve(a[1:], b[1:])
    return 1 + min(solve(a[1:], b), solve(a, b[1:]), solve(a[1:], b[1:]))
