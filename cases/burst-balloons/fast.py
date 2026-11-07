def solve(nums):
    vals = [1] + nums + [1]
    n = len(vals)
    best = [[0] * n for _ in range(n)]
    for width in range(2, n):
        for left in range(n - width):
            right = left + width
            for last in range(left + 1, right):
                gain = vals[left] * vals[last] * vals[right] + best[left][last] + best[last][right]
                best[left][right] = max(best[left][right], gain)
    return best[0][n - 1]
