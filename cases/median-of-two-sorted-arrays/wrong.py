"""Two wrong answers to hunt. Run the check first; README.md explains both behind a fold."""
from math import inf


def gut(a, b):
    """Average the median of each list."""
    def median(x):
        n = len(x)
        return x[n // 2] if n % 2 else (x[n // 2 - 1] + x[n // 2]) / 2
    if not a or not b:
        return float(median(a or b))
    return (median(a) + median(b)) / 2


# A copy of fast.py with exactly one line changed. Find it.
def planted(a, b):
    if len(a) > len(b):
        a, b = b, a
    m, n = len(a), len(b)
    half = (m + n) // 2
    lo, hi = 0, m
    while lo <= hi:
        i = (lo + hi) // 2
        j = half - i
        left_a = a[i - 1] if i > 0 else -inf
        right_a = a[i] if i < m else inf
        left_b = b[j - 1] if j > 0 else -inf
        right_b = b[j] if j < n else inf
        if left_a <= right_b and left_b <= right_a:
            if (m + n) % 2:
                return float(max(left_a, left_b))
            return (max(left_a, left_b) + min(right_a, right_b)) / 2
        if left_a > right_b:
            hi = i - 1
        else:
            lo = i + 1
