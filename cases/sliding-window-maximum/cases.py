"""Input generator for sliding-window-maximum. `generate` makes small inputs for the slow machine; `big` makes one large input for fast, and `big_check` tests the answer to it."""
from checking import strict_equal

TITLE = "Sliding Window Maximum"
FAMILY = "Sliding window"
LEETCODE = (239, "sliding-window-maximum")

MAX_SIZE = 9


def generate(rng, size):
    nums = [rng.randint(-5, 5) for _ in range(size + 1)]
    return (nums, rng.randint(1, len(nums)))


def edges():
    return [([-2**31], 1), ([-2**31, -2**31 + 1], 2), ([2**31 - 1, -2**31, -2**31], 1)]


def big(rng):
    return ([rng.randint(-1000, 1000) for _ in range(200000)], 5000)


def big_check(args, got):
    """Split into blocks of k and combine each block's running maximum from both sides, with no deque."""
    nums, k = args
    n = len(nums)
    left, right = nums[:], nums[:]
    for i in range(1, n):
        if i % k:
            left[i] = max(left[i - 1], nums[i])
    for i in range(n - 2, -1, -1):
        if (i + 1) % k:
            right[i] = max(right[i + 1], nums[i])
    return strict_equal(got, [max(right[i], left[i + k - 1]) for i in range(n - k + 1)])
