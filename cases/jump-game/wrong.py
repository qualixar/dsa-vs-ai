"""Two wrong answers to hunt. Run the check first; README.md explains both behind a fold."""


def gut(nums):
    """Always take the longest jump allowed from where you stand."""
    i = 0
    while i < len(nums) - 1:
        if nums[i] == 0:
            return False
        i += nums[i]
    return True


# A copy of fast.py with exactly one line changed. Find it.
def planted(nums):
    reach = 0
    for i, jump in enumerate(nums):
        if i > reach:
            return False
        reach = i + jump
    return True
