"""LeetCode 42, Trapping Rain Water: the famous control problem.

Limits from LeetCode (pulled 4 Nov 2026): 1 <= n <= 2*10^4, 0 <= height[i] <= 10^5.
"""
import random

METHOD = "trap"
SEED = 42_2026


def reference(height):
    """Slow and obviously correct: water above each bar is
    min(tallest bar to its left, tallest bar to its right) - its own height."""
    total = 0
    for i, h in enumerate(height):
        left = max(height[: i + 1])
        right = max(height[i:])
        total += min(left, right) - h
    return total


def fast(height):
    """Our own two-pointer solution. Used only to compute expected answers
    for the scale gate after the self-tests prove it equals the reference."""
    lo, hi = 0, len(height) - 1
    left_max = right_max = water = 0
    while lo < hi:
        if height[lo] <= height[hi]:
            left_max = max(left_max, height[lo])
            water += left_max - height[lo]
            lo += 1
        else:
            right_max = max(right_max, height[hi])
            water += right_max - height[hi]
            hi -= 1
    return water


def examples():
    return [([[0, 1, 0, 2, 1, 0, 1, 3, 2, 1, 2, 1]], 6), ([[4, 2, 0, 3, 2, 5]], 9)]


def edge_cases():
    return [
        [[0]], [[5]], [[2, 0]], [[0, 0, 0]], [[3, 0, 3]],
        [[1, 2, 3, 4, 5]], [[5, 4, 3, 2, 1]], [[5, 0, 0, 0, 5]],
        [[100000, 0, 100000]], [[2, 1, 2, 1, 2]], [[0, 7, 0, 0, 7, 0]],
    ]


def random_cases(count=3000, seed=SEED):
    rng = random.Random(seed)
    cases = []
    for _ in range(count):
        n = rng.randint(1, 12)
        top = rng.choice([1, 3, 6, 10])
        cases.append([[rng.randint(0, top) for _ in range(n)]])
    return cases


def medium_cases(count=600, seed=SEED):
    """Lengths 13-500, between the small and the full-size tests."""
    rng = random.Random(seed + 2)
    cases = [[[3] + [0] * 11 + [3]]]
    for _ in range(count - 1):
        n = rng.randint(13, 500)
        top = rng.choice([1, 5, 50, 100_000])
        cases.append([[rng.randint(0, top) for _ in range(n)]])
    return cases


def scale_cases(seed=SEED):
    rng = random.Random(seed + 1)
    n, top = 20_000, 100_000
    mountain = list(range(0, n // 2)) + list(range(n // 2, 0, -1))
    valley = [top - min(i, n - 1 - i) for i in range(n)]
    return [
        ("random", [[rng.randint(0, top) for _ in range(n)]]),
        ("valley", [valley]),
        ("mountain", [mountain]),
        ("zigzag", [[top if i % 2 else 0 for i in range(n)]]),
        ("flat", [[7] * n]),
        ("two-walls", [[top] + [0] * (n - 2) + [top]]),
    ]


def sanity(args, out):
    """Gate 3: an answer that breaks these rules is wrong for any input."""
    height = args[0]
    if not isinstance(out, int) or isinstance(out, bool):
        return "answer is not an integer"
    if out < 0:
        return "negative water"
    if out > len(height) * max(height):
        return "more water than the hall can hold"
    return None
