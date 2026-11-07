"""Two wrong answers to hunt. Run the check first; README.md explains both behind a fold."""


def gut(n):
    """An odd number adds a 1 to the number before it. An even number keeps the same count."""
    bits = [0] * (n + 1)
    for i in range(1, n + 1):
        bits[i] = bits[i - 1] + (i & 1)
    return bits


# A copy of fast.py with exactly one line changed. Find it.
def planted(n):
    bits = [0] * (n + 1)
    for i in range(1, n + 1):
        bits[i] = bits[i >> 1] + 1
    return bits
