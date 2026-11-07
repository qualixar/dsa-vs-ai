"""Input generator for number-of-islands. `generate` makes small inputs for the slow machine; `big` makes one large input for fast, and `big_check` tests the answer to it."""
from checking import strict_equal

TITLE = "Number of Islands"
FAMILY = "Graphs"
LEETCODE = (200, "number-of-islands")

MAX_SIZE = 5


def generate(rng, size):
    rows, cols = rng.randint(1, size + 1), rng.randint(1, size + 1)
    return ([[rng.randint(0, 1) for _ in range(cols)] for _ in range(rows)],)


def big(rng):
    return ([[1 if rng.random() < 0.6 else 0 for _ in range(300)] for _ in range(300)],)


def big_check(args, got):
    """Union-find instead of a flood fill."""
    grid = args[0]
    rows, cols = len(grid), len(grid[0])
    parent = list(range(rows * cols))
    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x
    land = 0
    for r in range(rows):
        for c in range(cols):
            if grid[r][c] == 1:
                land += 1
                for a, b in ((r - 1, c), (r, c - 1)):
                    if a >= 0 and b >= 0 and grid[a][b] == 1:
                        x, y = find(r * cols + c), find(a * cols + b)
                        if x != y:
                            parent[x] = y
                            land -= 1
    return strict_equal(got, land)
