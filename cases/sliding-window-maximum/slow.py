def solve(nums, k):
    """Take the maximum of every window."""
    return [max(nums[i:i + k]) for i in range(len(nums) - k + 1)]
