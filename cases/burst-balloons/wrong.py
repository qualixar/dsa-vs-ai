"""Two wrong answers to hunt. Run the check first; README.md explains both behind a fold."""


def gut(nums):
    """Always burst the smallest balloon first."""
    nums = list(nums)
    total = 0
    while nums:
        i = nums.index(min(nums))
        left = nums[i - 1] if i > 0 else 1
        right = nums[i + 1] if i + 1 < len(nums) else 1
        total += left * nums[i] * right
        del nums[i]
    return total


# A copy of fast.py with exactly one line changed. Find it.
def planted(nums):
    vals = [1] + nums + [1]
    n = len(vals)
    best = [[0] * n for _ in range(n)]
    for width in range(2, n):
        for left in range(n - width):
            right = left + width
            for last in range(left + 1, right):
                gain = vals[last - 1] * vals[last] * vals[last + 1] + best[left][last] + best[last][right]
                best[left][right] = max(best[left][right], gain)
    return best[0][n - 1]
