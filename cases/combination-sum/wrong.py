"""Two wrong answers to hunt. Run the check first; README.md explains both behind a fold."""


def gut(candidates, target):
    """At every step try every candidate."""
    out = []
    def walk(left, picked):
        if left == 0:
            out.append(picked)
            return
        for c in candidates:
            if c <= left:
                walk(left - c, picked + [c])
    walk(target, [])
    return out


# A copy of fast.py with exactly one line changed. Find it.
def planted(candidates, target):
    out = []
    picked = []
    def walk(start, left):
        if left == 0:
            out.append(picked[:])
            return
        for i in range(start, len(candidates)):
            if candidates[i] <= left:
                picked.append(candidates[i])
                walk(i + 1, left - candidates[i])
                picked.pop()
    walk(0, target)
    return out
