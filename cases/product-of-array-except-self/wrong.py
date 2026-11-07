"""Two wrong answers to hunt. Run the check first; README.md explains both behind a fold."""


def gut(nums):
    """Multiply everything once, then divide out each number. A zero gets a zero."""
    total = 1
    for x in nums:
        total *= x
    return [total // x if x else 0 for x in nums]


# A copy of fast.py with exactly one line changed. Find it.
def planted(nums):
    out = [1] * len(nums)
    left = 1
    for i, x in enumerate(nums):
        out[i] = left
        left *= x
    right = 1
    for i in range(len(nums) - 1, 0, -1):
        out[i] *= right
        right *= nums[i]
    return out
