"""Input generator for evaluate-reverse-polish-notation. `generate` makes small inputs for the slow machine; `big` makes one large input for fast, and `big_check` tests the answer to it."""
from checking import strict_equal

TITLE = "Evaluate Reverse Polish Notation"
FAMILY = "Stacks"
LEETCODE = (150, "evaluate-reverse-polish-notation")

MAX_SIZE = 6


def _divide(a, b):
    q = abs(a) // abs(b)
    return q if (a < 0) == (b < 0) else -q


def generate(rng, size):
    """Build a valid expression of any nesting. An operator that would divide by zero becomes a plus."""
    items, values = [], []
    to_push = size + 1
    while to_push or len(values) > 1:
        if to_push and (len(values) < 2 or rng.random() < 0.5):
            value = rng.randint(-9, 9)
            items.append(str(value))
            values.append(value)
            to_push -= 1
        else:
            b, a = values.pop(), values.pop()
            op = rng.choice("+-*/")
            if op == "/" and b == 0:
                op = "+"
            items.append(op)
            values.append(a + b if op == "+" else a - b if op == "-" else a * b if op == "*" else _divide(a, b))
    return (items,)


def edges():
    return [(["2147483647", "-2147483648", "+"],), (["2147483647", "1", "/"],), (["-2147483648", "1", "*"],)]


def big(rng):
    items = ["1"]
    for _ in range(50000):
        items += ["2", "+", "1", "-", "2", "*", "2", "/"]
    return (items,)


def big_check(args, got):
    """Each repeat adds 2, takes away 1, then doubles and halves, for a net gain of 1."""
    return strict_equal(got, 50001)
