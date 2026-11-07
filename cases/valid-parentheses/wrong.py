"""Two wrong answers to hunt. Run the check first; README.md explains both behind a fold."""


def gut(s):
    """Each kind of bracket has as many openers as closers."""
    return all(s.count(a) == s.count(b) for a, b in ("()", "[]", "{}"))


# A copy of fast.py with exactly one line changed. Find it.
def planted(s):
    closers = {")": "(", "]": "[", "}": "{"}
    stack = []
    for c in s:
        if c in closers:
            if not stack or stack.pop() != closers[c]:
                return False
        else:
            stack.append(c)
    return True
