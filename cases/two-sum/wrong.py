"""Two wrong answers to hunt. Run the check first; README.md explains both behind a fold."""


def gut(nums, target):
    """Sort, then walk in from both ends."""
    nums = sorted(nums)
    lo, hi = 0, len(nums) - 1
    while lo < hi:
        total = nums[lo] + nums[hi]
        if total == target:
            return [lo, hi]
        if total < target:
            lo += 1
        else:
            hi -= 1
    return None


# A copy of fast.py with exactly one line changed. Find it.
def planted(nums, target):
    seen = {nums[0]: 0}
    for i, x in enumerate(nums):
        if target - x in seen:
            return [seen[target - x], i]
        seen[x] = i
    return None
