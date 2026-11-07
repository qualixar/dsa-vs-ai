"""Two wrong answers to hunt. Run the check first; README.md explains both behind a fold."""


def gut(heights):
    """Find the peaks, then fill each valley between two neighbouring peaks."""
    n = len(heights)
    peaks = [i for i in range(n) if (i == 0 or heights[i] >= heights[i - 1]) and (i == n - 1 or heights[i] >= heights[i + 1])]
    water = 0
    for a, b in zip(peaks, peaks[1:]):
        level = min(heights[a], heights[b])
        water += sum(max(0, level - heights[i]) for i in range(a + 1, b))
    return water


# A copy of fast.py with exactly one line changed. Find it.
def planted(heights):
    lo, hi = 0, len(heights) - 1
    left_max = right_max = water = 0
    while lo < hi - 1:
        if heights[lo] < heights[hi]:
            left_max = max(left_max, heights[lo])
            water += left_max - heights[lo]
            lo += 1
        else:
            right_max = max(right_max, heights[hi])
            water += right_max - heights[hi]
            hi -= 1
    return water
