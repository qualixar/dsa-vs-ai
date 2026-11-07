def solve(nums):
    """Spread out from position 0, trying every jump length from every position reached."""
    reached = {0}
    stack = [0]
    while stack:
        i = stack.pop()
        for step in range(1, nums[i] + 1):
            if i + step < len(nums) and i + step not in reached:
                reached.add(i + step)
                stack.append(i + step)
    return len(nums) - 1 in reached
