def _divide(a, b):
    q = abs(a) // abs(b)
    return q if (a < 0) == (b < 0) else -q


def solve(items):
    """Rewrite the list: find a number, number, operator triple, replace it with its value, and repeat."""
    items = list(items)
    while len(items) > 1:
        for i in range(len(items) - 2):
            a, b, op = items[i], items[i + 1], items[i + 2]
            if op in ("+", "-", "*", "/") and a not in ("+", "-", "*", "/") and b not in ("+", "-", "*", "/"):
                x, y = int(a), int(b)
                value = x + y if op == "+" else x - y if op == "-" else x * y if op == "*" else _divide(x, y)
                items[i:i + 3] = [str(value)]
                break
    return int(items[0])
