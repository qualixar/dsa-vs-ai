"""A slow machine for a problem outside the library, in one file, with no dependencies.

The problem: find the largest sum of a contiguous, non-empty stretch of a list.

  python3 docs/examples/own_check.py

It exits 1 and prints the smallest input that breaks `answer`. Replace `answer` with the code you want to check.
"""
import random
import sys


def slow(nums):
    """Add up every stretch. Nobody needs convincing that this is right, and that is the whole point."""
    return max(sum(nums[i:j + 1]) for i in range(len(nums)) for j in range(i, len(nums)))


def answer(nums):
    """The code under check. It looks right, and it is right whenever some number is positive."""
    best = current = 0
    for x in nums:
        current = max(0, current + x)
        best = max(best, current)
    return best


def main():
    rng = random.Random(1)
    failures = []
    for _ in range(3000):
        nums = [rng.randint(-5, 5) for _ in range(rng.randint(1, 8))]
        if answer(nums) != slow(nums):
            failures.append(nums)
    if not failures:
        print("no disagreement on 3000 inputs, which is not the same as correct")
        return 0
    smallest = min(failures, key=len)
    print(f"{len(failures)} of 3000 inputs disagree")
    print(f"smallest failing input: {smallest}")
    print(f"answer says {answer(smallest)}, slow says {slow(smallest)}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
