"""A sample answer for the two-sum case, with a bug in it, to show what a failing check looks like.

  python3 check.py two-sum --answer docs/examples/answer_with_a_bug.py
"""


def solve(nums, target):
    seen = {}
    for i, x in enumerate(nums):
        seen[x] = i
        if target - x in seen:
            return [seen[target - x], i]
    return None
