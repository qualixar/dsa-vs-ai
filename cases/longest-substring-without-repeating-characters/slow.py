def solve(s):
    """Test every stretch of the string."""
    best = 0
    for i in range(len(s)):
        for j in range(i, len(s)):
            part = s[i:j + 1]
            if len(set(part)) == len(part):
                best = max(best, len(part))
    return best
