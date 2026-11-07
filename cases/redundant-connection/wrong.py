"""Two wrong answers to hunt. Run the check first; README.md explains both behind a fold."""


def gut(edges):
    """The first edge whose two ends have both been seen before closes the loop."""
    seen = set()
    for a, b in edges:
        if a in seen and b in seen:
            return [a, b]
        seen.update((a, b))


# A copy of fast.py with exactly one line changed. Find it.
def planted(edges):
    parent = list(range(len(edges) + 1))
    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x
    for a, b in edges:
        ra, rb = find(a), find(b)
        if ra == rb:
            return [a, b]
        parent[a] = rb
