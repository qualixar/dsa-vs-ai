from functools import lru_cache
class Solution:
    def elevatorRequests(self, n: int, start: int, requests: list[int]) -> int:
        left = sorted((r for r in requests if r < start), reverse=True)
        right = sorted(r for r in requests if r > start)
        a, b = len(left), len(right)
        k = a + b

        @lru_cache(maxsize=None)
        def go(i, j, side):
            pos = start if i + j == 0 else (left[i - 1] if side == 0 else right[j - 1])
            w = k - i - j
            if w == 0:
                return 0
            best = float("inf")
            if i < a:
                best = min(best, abs(pos - left[i]) * w + go(i + 1, j, 0))
            if j < b:
                best = min(best, abs(right[j] - pos) * w + go(i, j + 1, 1))
            return best

        return go(0, 0, 0)
