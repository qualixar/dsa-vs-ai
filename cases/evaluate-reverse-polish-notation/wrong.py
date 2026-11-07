"""Two wrong answers to hunt. Run the check first; README.md explains both behind a fold."""


def gut(items):
    """Stack machine using Python's // for division."""
    stack = []
    for item in items:
        if item in ("+", "-", "*", "/"):
            b = stack.pop()
            a = stack.pop()
            stack.append(a + b if item == "+" else a - b if item == "-" else a * b if item == "*" else a // b)
        else:
            stack.append(int(item))
    return stack[0]


# A copy of fast.py with exactly one line changed. Find it.
def planted(items):
    stack = []
    for item in items:
        if item in ("+", "-", "*", "/"):
            b = stack.pop()
            a = stack.pop()
            if item == "+":
                stack.append(a + b)
            elif item == "-":
                stack.append(b - a)
            elif item == "*":
                stack.append(a * b)
            else:
                q = abs(a) // abs(b)
                stack.append(q if (a < 0) == (b < 0) else -q)
        else:
            stack.append(int(item))
    return stack[0]
