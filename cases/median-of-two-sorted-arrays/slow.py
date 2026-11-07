def solve(a, b):
    """Merge by sorting, then read the middle."""
    merged = sorted(a + b)
    n = len(merged)
    if n % 2:
        return float(merged[n // 2])
    return (merged[n // 2 - 1] + merged[n // 2]) / 2
