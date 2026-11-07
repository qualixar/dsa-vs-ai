"""Two wrong answers to hunt. Run the check first; README.md explains both behind a fold."""


def gut(nums):
    """Sort large to small and add each number to the lighter side."""
    left = right = 0
    for x in sorted(nums, reverse=True):
        if left <= right:
            left += x
        else:
            right += x
    return left == right


# A copy of fast.py with exactly one line changed. Find it.
def planted(nums):
    total = sum(nums)
    if total % 2:
        return False
    target = total // 2
    can = [True] + [False] * target
    for x in nums:
        for s in range(x, target + 1):
            can[s] = can[s] or can[s - x]
    return can[target]
