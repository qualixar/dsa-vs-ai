def solve(nums, k):
    """Sort everything."""
    return sorted(nums, reverse=True)[k - 1]
