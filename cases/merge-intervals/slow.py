def solve(intervals):
    """Keep merging any two that touch until none do."""
    items = [list(i) for i in intervals]
    changed = True
    while changed:
        changed = False
        for i in range(len(items)):
            for j in range(i + 1, len(items)):
                if items[i][0] <= items[j][1] and items[j][0] <= items[i][1]:
                    items[i] = [min(items[i][0], items[j][0]), max(items[i][1], items[j][1])]
                    del items[j]
                    changed = True
                    break
            if changed:
                break
    return sorted(items)
