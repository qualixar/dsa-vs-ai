def solve(root):
    """Start a walk from every node and follow every direction, adding as you go."""
    links = {}
    stack = [root]
    while stack:
        node = stack.pop()
        links.setdefault(id(node), (node, []))
        for child in (node.left, node.right):
            if child:
                links.setdefault(id(child), (child, []))
                links[id(node)][1].append(child)
                links[id(child)][1].append(node)
                stack.append(child)
    best = root.val
    def walk(node, came_from, total):
        nonlocal best
        total += node.val
        best = max(best, total)
        for other in links[id(node)][1]:
            if other is not came_from:
                walk(other, node, total)
    for node, _ in links.values():
        walk(node, None, 0)
    return best
