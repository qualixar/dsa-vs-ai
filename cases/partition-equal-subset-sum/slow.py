def solve(nums):
    """Try every subset."""
    total = sum(nums)
    for mask in range(1 << len(nums)):
        if 2 * sum(x for i, x in enumerate(nums) if mask >> i & 1) == total:
            return True
    return False
