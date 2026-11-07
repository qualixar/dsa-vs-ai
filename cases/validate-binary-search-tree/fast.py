from math import inf


def solve(root):
    def valid(node, low, high):
        if node is None:
            return True
        if not low < node.val < high:
            return False
        return valid(node.left, low, node.val) and valid(node.right, node.val, high)
    return valid(root, -inf, inf)
