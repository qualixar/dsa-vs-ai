def solve(capacity, ops):
    """A plain list of [key, value], most recent last. Every step scans it."""
    items = []
    out = []
    for op in ops:
        key = op[1]
        hit = next((p for p in items if p[0] == key), None)
        if op[0] == "get":
            if hit:
                items.remove(hit)
                items.append(hit)
            out.append(hit[1] if hit else -1)
        else:
            if hit:
                items.remove(hit)
            items.append([key, op[2]])
            if len(items) > capacity:
                del items[0]
    return out
