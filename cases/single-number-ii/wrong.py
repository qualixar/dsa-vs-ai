"""Two wrong answers to hunt. Run the check first; README.md explains both behind a fold."""


def gut(nums):
    """XOR everything, which is how the version with pairs is solved."""
    answer = 0
    for x in nums:
        answer ^= x
    return answer


# A copy of fast.py with exactly one line changed. Find it.
def planted(nums):
    answer = 0
    for bit in range(32):
        count = sum((x >> bit) & 1 for x in nums)
        if count % 3:
            answer |= 1 << bit
    if answer > 1 << 32:
        answer -= 1 << 32
    return answer
