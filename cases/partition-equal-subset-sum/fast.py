def solve(nums):
    total = sum(nums)
    if total % 2:
        return False
    target = total // 2
    can = [True] + [False] * target
    for x in nums:
        for s in range(target, x - 1, -1):
            can[s] = can[s] or can[s - x]
    return can[target]
