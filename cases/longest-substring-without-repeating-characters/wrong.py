"""Two wrong answers to hunt. Run the check first; README.md explains both behind a fold."""


def gut(s):
    """Grow a run; when a letter repeats, begin a new run from that letter."""
    best = 0
    run = set()
    for c in s:
        if c in run:
            run = set()
        run.add(c)
        best = max(best, len(run))
    return best


# A copy of fast.py with exactly one line changed. Find it.
def planted(s):
    last = {}
    start = best = 0
    for i, c in enumerate(s):
        if c in last:
            start = last[c] + 1
        last[c] = i
        best = max(best, i - start + 1)
    return best
