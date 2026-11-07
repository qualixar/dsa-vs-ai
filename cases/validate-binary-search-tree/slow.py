def solve(root):
    """At every node, compare against every value on each side of it."""
    def values(node):
        return [] if node is None else values(node.left) + [node.val] + values(node.right)
    def check(node):
        if node is None:
            return True
        if any(v >= node.val for v in values(node.left)) or any(v <= node.val for v in values(node.right)):
            return False
        return check(node.left) and check(node.right)
    return check(root)
