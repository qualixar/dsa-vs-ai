def solve(nums, target):
    """Look at every position."""
    for i, x in enumerate(nums):
        if x == target:
            return i
    return -1
