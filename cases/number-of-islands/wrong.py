"""Two wrong answers to hunt. Run the check first; README.md explains both behind a fold."""


def gut(grid):
    """Count top-left corners: land cells with no land above them or to their left."""
    count = 0
    for r, row in enumerate(grid):
        for c, cell in enumerate(row):
            if cell == 1 and not (r > 0 and grid[r - 1][c] == 1) and not (c > 0 and row[c - 1] == 1):
                count += 1
    return count


# A copy of fast.py with exactly one line changed. Find it.
def planted(grid):
    rows, cols = len(grid), len(grid[0])
    seen = set()
    count = 0
    for r in range(rows):
        for c in range(cols):
            if grid[r][c] == 1 and (r, c) not in seen:
                count += 1
                seen.add((r, c))
                stack = [(r, c)]
                while stack:
                    x, y = stack.pop()
                    for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                        if 0 < nx < rows and 0 <= ny < cols and grid[nx][ny] == 1 and (nx, ny) not in seen:
                            seen.add((nx, ny))
                            stack.append((nx, ny))
    return count
