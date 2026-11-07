def solve(nums, k):
    total = sum(nums)
    if total % k:
        return False
    side = total // k
    n = len(nums)
    fill = [-1] * (1 << n)
    fill[0] = 0
    for mask in range(1 << n):
        if fill[mask] < 0:
            continue
        for i in range(n):
            bit = 1 << i
            if not mask & bit and fill[mask] + nums[i] <= side:
                fill[mask | bit] = (fill[mask] + nums[i]) % side
    return fill[-1] == 0
