def solve(edges):
    """From the last edge backward, remove it and see if everything is still connected."""
    n = len(edges)
    for skip in range(n - 1, -1, -1):
        near = {i: [] for i in range(1, n + 1)}
        for i, (a, b) in enumerate(edges):
            if i != skip:
                near[a].append(b)
                near[b].append(a)
        seen = {1}
        stack = [1]
        while stack:
            for other in near[stack.pop()]:
                if other not in seen:
                    seen.add(other)
                    stack.append(other)
        if len(seen) == n:
            return edges[skip]
