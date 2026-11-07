def solve(nums):
    """Count every value by scanning the list."""
    for x in nums:
        if nums.count(x) == 1:
            return x
