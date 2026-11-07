def solve(heights):
    """For each bar, the water above it is set by the tallest bar on each side."""
    water = 0
    for i, h in enumerate(heights):
        water += min(max(heights[:i + 1]), max(heights[i:])) - h
    return water
