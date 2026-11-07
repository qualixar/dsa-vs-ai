"""Two wrong answers to hunt. Run the check first; README.md explains both behind a fold."""
from math import inf


def gut(root):
    """Best downward path from any node, with no bend at the top."""
    best = -inf
    def gain(node):
        nonlocal best
        if node is None:
            return 0
        here = node.val + max(gain(node.left), gain(node.right), 0)
        best = max(best, here)
        return here
    gain(root)
    return best


# A copy of fast.py with exactly one line changed. Find it.
def planted(root):
    best = -inf
    def gain(node):
        nonlocal best
        if node is None:
            return 0
        left = gain(node.left)
        right = max(gain(node.right), 0)
        best = max(best, node.val + left + right)
        return node.val + max(left, right)
    gain(root)
    return best
