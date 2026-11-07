def solve(a, b):
    row = list(range(len(b) + 1))
    for i, x in enumerate(a, 1):
        prev, row[0] = row[0], i
        for j, y in enumerate(b, 1):
            cost = 0 if x == y else 1
            prev, row[j] = row[j], min(row[j] + 1, row[j - 1] + 1, prev + cost)
    return row[-1]
