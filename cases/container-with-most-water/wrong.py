"""Two wrong answers to hunt. Run the check first; README.md explains both behind a fold."""


def gut(heights):
    """Take the two tallest lines."""
    order = sorted(range(len(heights)), key=lambda i: heights[i])
    a, b = order[-1], order[-2]
    return abs(a - b) * min(heights[a], heights[b])


# A copy of fast.py with exactly one line changed. Find it.
def planted(heights):
    lo, hi = 0, len(heights) - 1
    best = 0
    while lo < hi:
        best = max(best, (hi - lo) * min(heights[lo], heights[hi]))
        if heights[lo] > heights[hi]:
            lo += 1
        else:
            hi -= 1
    return best
