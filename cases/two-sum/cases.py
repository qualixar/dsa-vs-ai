"""Input generator for two-sum. `generate` makes small inputs for the slow machine; `big` makes one large input for fast, and `big_check` tests the answer to it."""
from checking import is_ints

TITLE = "Two Sum"
FAMILY = "Arrays and hashing"
LEETCODE = (1, "two-sum")

MAX_SIZE = 8


def generate(rng, size):
    return ([rng.randint(-5, 5) for _ in range(size + 2)], rng.randint(-8, 8))


def edges():
    return [([2**31 - 1, -2**31], -1), ([-2**31, 0, 2**31 - 1], -2**31), ([2**31 - 1, 2**31 - 1], 2**32 - 2)]


def big(rng):
    nums = rng.sample(range(10**7), 200000)
    return (nums, nums[-1] + nums[-2])


def big_check(args, got):
    """The last two numbers add up to the target by construction, so a pair exists. `same` tests the pair returned."""
    return same(args, got, [len(args[0]) - 2, len(args[0]) - 1])


def same(args, got, want):
    """Any valid pair counts, so test the pair itself: two whole numbers, in range, different, adding up."""
    nums, target = args
    if want is None:
        return got is None
    if not is_ints(got, 2):
        return False
    i, j = got
    return 0 <= i < len(nums) and 0 <= j < len(nums) and i != j and nums[i] + nums[j] == target
