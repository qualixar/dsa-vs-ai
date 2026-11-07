"""Two wrong answers to hunt. Run the check first; README.md explains both behind a fold."""


def gut(heights):
    """Either the tallest bar alone, or the shortest bar across the whole width."""
    return max(max(heights), min(heights) * len(heights))


# A copy of fast.py with exactly one line changed. Find it.
def planted(heights):
    stack = []
    best = 0
    for i, h in enumerate(heights + [0]):
        while stack and heights[stack[-1]] >= h:
            top = stack.pop()
            left = stack[-1] if stack else 0
            best = max(best, heights[top] * (i - left - 1))
        stack.append(i)
    return best
