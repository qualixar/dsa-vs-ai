"""Two wrong answers to hunt. Run the check first; README.md explains both behind a fold."""
import bisect


def gut(nums):
    """Start at the first number and take every number larger than the last one taken."""
    count = 0
    last = None
    for x in nums:
        if last is None or x > last:
            count += 1
            last = x
    return count


# A copy of fast.py with exactly one line changed. Find it.
def planted(nums):
    tails = []
    for x in nums:
        i = bisect.bisect_right(tails, x)
        if i == len(tails):
            tails.append(x)
        else:
            tails[i] = x
    return len(tails)
