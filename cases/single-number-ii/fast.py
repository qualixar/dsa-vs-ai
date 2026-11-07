def solve(nums):
    answer = 0
    for bit in range(32):
        count = sum((x >> bit) & 1 for x in nums)
        if count % 3:
            answer |= 1 << bit
    if answer >= 1 << 31:
        answer -= 1 << 32
    return answer
