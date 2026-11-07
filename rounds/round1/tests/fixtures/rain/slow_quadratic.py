class Solution:
    def trap(self, height: list[int]) -> int:
        total = 0
        for i, h in enumerate(height):
            total += min(max(height[: i + 1]), max(height[i:])) - h
        return total
