from collections import Counter


def solve(s, t):
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
            if need[s[lo]] > 0:
                missing += 1
            lo += 1
    return s[best_lo:best_lo + best_len] if best_len <= len(s) else ""
