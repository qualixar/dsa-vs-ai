"""Two wrong answers to hunt. Run the check first; README.md explains both behind a fold."""


def gut(nums, k):
    """Sort large to small and put each number in the first group with room."""
    total = sum(nums)
    if total % k:
        return False
    side = total // k
    groups = [0] * k
    for x in sorted(nums, reverse=True):
        for g in range(k):
            if groups[g] + x <= side:
                groups[g] += x
                break
        else:
            return False
    return True


# A copy of fast.py with exactly one line changed. Find it.
def planted(nums, k):
    total = sum(nums)
    if total % k:
        return False
    side = total // k
    n = len(nums)
    fill = [-1] * (1 << n)
    fill[0] = 0
    for mask in range(1 << n):
        if fill[mask] < 0:
            continue
        for i in range(n):
            bit = 1 << i
            if not mask & bit:
                fill[mask | bit] = (fill[mask] + nums[i]) % side
    return fill[-1] == 0
