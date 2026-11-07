"""Two wrong answers to hunt. Run the check first; README.md explains both behind a fold."""


def gut(nums, k):
    """Sliding window: grow on the right, shrink on the left when the sum is too big."""
    lo = total = answer = 0
    for hi, x in enumerate(nums):
        total += x
        while total > k and lo <= hi:
            total -= nums[lo]
            lo += 1
        if total == k:
            answer += 1
    return answer


# A copy of fast.py with exactly one line changed. Find it.
def planted(nums, k):
    counts = {}
    total = 0
    answer = 0
    for x in nums:
        total += x
        answer += counts.get(total - k, 0)
        counts[total] = counts.get(total, 0) + 1
    return answer
