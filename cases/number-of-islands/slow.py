def solve(grid):
    """Give each land cell its own label, then spread the smallest label around until nothing changes."""
    rows, cols = len(grid), len(grid[0])
    label = {(r, c): r * cols + c for r in range(rows) for c in range(cols) if grid[r][c] == 1}
    changed = True
    while changed:
        changed = False
        for (r, c) in label:
            for near in ((r + 1, c), (r - 1, c), (r, c + 1), (r, c - 1)):
                if near in label and label[near] < label[(r, c)]:
                    label[(r, c)] = label[near]
                    changed = True
    return len(set(label.values()))
