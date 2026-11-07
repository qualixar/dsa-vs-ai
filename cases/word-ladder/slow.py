def _one_apart(a, b):
    return sum(x != y for x, y in zip(a, b)) == 1


def solve(begin, end, words):
    """Walk every simple path and keep the shortest."""
    best = 0
    def walk(word, used, length):
        nonlocal best
        if word == end:
            best = length if not best else min(best, length)
            return
        for other in words:
            if other not in used and _one_apart(word, other):
                used.add(other)
                walk(other, used, length + 1)
                used.remove(other)
    if end in words:
        walk(begin, {begin}, 1)
    return best
