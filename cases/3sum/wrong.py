"""Two wrong answers to hunt. Run the check first; README.md explains both behind a fold."""


def gut(nums):
    """For each pair, look the third number up in a set of all values."""
    values = set(nums)
    found = set()
    for i in range(len(nums)):
        for j in range(i + 1, len(nums)):
            third = -nums[i] - nums[j]
            if third in values:
                found.add(tuple(sorted((nums[i], nums[j], third))))
    return [list(t) for t in found]


# A copy of fast.py with exactly one line changed. Find it.
def planted(nums):
    nums = sorted(nums)
    out = []
    for i in range(len(nums) - 2):
        if i + 1 < len(nums) and nums[i] == nums[i + 1]:
            continue
        lo, hi = i + 1, len(nums) - 1
        while lo < hi:
            total = nums[i] + nums[lo] + nums[hi]
            if total < 0:
                lo += 1
            elif total > 0:
                hi -= 1
            else:
                out.append([nums[i], nums[lo], nums[hi]])
                lo += 1
                while lo < hi and nums[lo] == nums[lo - 1]:
                    lo += 1
    return out
