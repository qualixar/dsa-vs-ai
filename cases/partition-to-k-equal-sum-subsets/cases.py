"""Input generator for partition-to-k-equal-sum-subsets. `generate` makes small inputs for the slow machine; `big` makes one large input for fast, and `big_check` tests the answer to it."""
from checking import strict_equal

TITLE = "Partition to K Equal Sum Subsets"
FAMILY = "DP: bitmask"
LEETCODE = (698, "partition-to-k-equal-sum-subsets")

MAX_SIZE = 6


def generate(rng, size):
    return ([rng.randint(1, 6) for _ in range(size + 2)], rng.randint(1, 3))


def big(rng):
    nums = [rng.randint(1, 30) for _ in range(15)]
    nums[0] += 3 - sum(nums) % 3
    return (nums, 3)


def big_check(args, got):
    """Backtracking over groups, largest numbers first, with no bitmask table."""
    nums, k = args
    total = sum(nums)
    if total % k:
        return strict_equal(got, False)
    side = total // k
    nums = sorted(nums, reverse=True)
    groups = [0] * k
    def place(i):
        if i == len(nums):
            return True
        tried = set()
        for g in range(k):
            if groups[g] + nums[i] <= side and groups[g] not in tried:
                tried.add(groups[g])
                groups[g] += nums[i]
                if place(i + 1):
                    return True
                groups[g] -= nums[i]
        return False
    return strict_equal(got, place(0))
