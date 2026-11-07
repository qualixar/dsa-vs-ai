"""Two wrong answers to hunt. Run the check first; README.md explains both behind a fold."""
from math import inf


def gut(root):
    """Each node is larger than its left child and smaller than its right child."""
    if root is None:
        return True
    if root.left and root.left.val >= root.val:
        return False
    if root.right and root.right.val <= root.val:
        return False
    return gut(root.left) and gut(root.right)


# A copy of fast.py with exactly one line changed. Find it.
def planted(root):
    def valid(node, low, high):
        if node is None:
            return True
        if not low <= node.val <= high:
            return False
        return valid(node.left, low, node.val) and valid(node.right, node.val, high)
    return valid(root, -inf, inf)
