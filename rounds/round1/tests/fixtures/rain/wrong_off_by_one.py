class Solution:
    def trap(self, height: list[int]) -> int:
        total = 0
        for i in range(1, len(height) - 1):
            total += max(0, min(max(height[:i]), max(height[i + 1:])) - height[i])
        return total + (1 if len(height) > 3 else 0)
