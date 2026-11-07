from collections import Counter


def solve(s, t):
    """Test every stretch of s."""
    need = Counter(t)
    best = ""
    for i in range(len(s)):
        for j in range(i, len(s)):
            part = s[i:j + 1]
            if not need - Counter(part) and (not best or len(part) < len(best)):
                best = part
    return best
