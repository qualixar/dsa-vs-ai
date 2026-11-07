class Solution:
    def trap(self, height: List[int]) -> int:
        lo, hi, lm, rm, w = 0, len(height) - 1, 0, 0, 0
        while lo < hi:
            if height[lo] <= height[hi]:
                lm = max(lm, height[lo]); w += lm - height[lo]; lo += 1
            else:
                rm = max(rm, height[hi]); w += rm - height[hi]; hi -= 1
        return w
