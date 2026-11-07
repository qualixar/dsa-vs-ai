from itertools import permutations


def solve(n, prereqs):
    """Try every order."""
    for order in permutations(range(n)):
        where = {c: i for i, c in enumerate(order)}
        if all(where[need] < where[course] for course, need in prereqs):
            return list(order)
    return []
