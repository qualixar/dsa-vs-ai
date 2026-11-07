"""Two wrong answers to hunt. Run the check first; README.md explains both behind a fold."""
from collections import Counter


def gut(s, t):
    """Extend until t is covered, trim the left edge, and take that window."""
    need = Counter(t)
    for hi in range(len(s)):
        if not need - Counter(s[:hi + 1]):
            lo = 0
            while not need - Counter(s[lo + 1:hi + 1]):
                lo += 1
            return s[lo:hi + 1]
    return ""


# A copy of fast.py with exactly one line changed. Find it.
def planted(s, t):
    need = Counter(t)
    missing = len(t)
    best_lo, best_len = 0, len(s) + 1
    lo = 0
    for hi, c in enumerate(s):
        if need[c] > 0:
            missing -= 1
        need[c] -= 1
        while missing == 0:
            if hi - lo + 1 < best_len:
                best_lo, best_len = lo, hi - lo + 1
            need[s[lo]] += 1
            if need[s[lo]] >= 0:
                missing += 1
            lo += 1
    return s[best_lo:best_lo + best_len] if best_len <= len(s) else ""
