def solve(nums):
    """Try every order of bursting."""
    if not nums:
        return 0
    best = 0
    for i, x in enumerate(nums):
        left = nums[i - 1] if i > 0 else 1
        right = nums[i + 1] if i + 1 < len(nums) else 1
        best = max(best, left * x * right + solve(nums[:i] + nums[i + 1:]))
    return best
