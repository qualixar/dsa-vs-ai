"""Two wrong answers to hunt. Run the check first; README.md explains both behind a fold."""
from collections import deque


def gut(nums, k):
    """Remember the current best. When it leaves the window, take the newest number."""
    out = []
    best, where = None, -1
    for i, x in enumerate(nums):
        if best is None or x >= best or where <= i - k:
            best, where = x, i
        if i >= k - 1:
            out.append(best)
    return out


# A copy of fast.py with exactly one line changed. Find it.
def planted(nums, k):
    window = deque()
    out = []
    for i, x in enumerate(nums):
        while window and nums[window[-1]] <= x:
            window.pop()
        window.append(i)
        if window[0] < i - k:
            window.popleft()
        if i >= k - 1:
            out.append(nums[window[0]])
    return out
