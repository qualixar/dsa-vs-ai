"""Input generator for binary-tree-maximum-path-sum. `generate` makes small inputs for the slow machine; `big` makes one large input for fast, and `big_check` tests the answer to it."""
from checking import strict_equal
from structures import TreeNode, random_tree

TITLE = "Binary Tree Maximum Path Sum"
FAMILY = "Trees"
LEETCODE = (124, "binary-tree-maximum-path-sum")

MAX_SIZE = 7


def generate(rng, size):
    return (random_tree(rng, size + 1, lambda: rng.randint(-6, 6)),)


def edges():
    return [(TreeNode(-2**31),), (TreeNode(2**31 - 1),), (TreeNode(-2**31, TreeNode(-2**31)),)]


def big(rng):
    nodes = [TreeNode(rng.randint(-100, 100)) for _ in range((1 << 17) - 1)]
    for i, node in enumerate(nodes):
        if 2 * i + 2 < len(nodes):
            node.left, node.right = nodes[2 * i + 1], nodes[2 * i + 2]
    return (nodes[0],)


def big_check(args, got):
    """The tree is complete, so read it into an array and work from the leaves up, with no recursion."""
    values, level = [], [args[0]]
    for node in level:
        values.append(node.val)
        if node.left:
            level += [node.left, node.right]
    n = len(values)
    gain = [0] * (n + 2)
    best = None
    for i in range(n - 1, -1, -1):
        left = max(gain[2 * i + 1], 0) if 2 * i + 1 < n else 0
        right = max(gain[2 * i + 2], 0) if 2 * i + 2 < n else 0
        gain[i] = values[i] + max(left, right)
        total = values[i] + left + right
        best = total if best is None else max(best, total)
    return strict_equal(got, best)
