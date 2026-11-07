"""Input generator for validate-binary-search-tree. `generate` makes small inputs for the slow machine; `big` makes one large input for fast, and `big_check` tests the answer to it."""
from checking import strict_equal
from structures import TreeNode, random_tree

TITLE = "Validate Binary Search Tree"
FAMILY = "Trees"
LEETCODE = (98, "validate-binary-search-tree")

MAX_SIZE = 7


def _insert(root, value):
    if root is None:
        return TreeNode(value)
    node = root
    while True:
        side = "left" if value < node.val else "right"
        if getattr(node, side) is None:
            setattr(node, side, TreeNode(value))
            return root
        node = getattr(node, side)


def generate(rng, size):
    """Mostly a real search tree, with one value often disturbed. Otherwise a random shape."""
    if rng.random() < 0.3:
        return (random_tree(rng, size, lambda: rng.randint(-5, 5)),)
    root = None
    nodes = []
    for value in rng.sample(range(-6, 7), size):
        root = _insert(root, value)
    stack = [root] if root else []
    while stack:
        node = stack.pop()
        nodes.append(node)
        stack += [c for c in (node.left, node.right) if c]
    if nodes and rng.random() < 0.6:
        rng.choice(nodes).val = rng.randint(-6, 7)
    return (root,)


def edges():
    return [(TreeNode(-2**31),), (TreeNode(2**31 - 1),), (TreeNode(0, TreeNode(-2**31), TreeNode(2**31 - 1)),),
            (TreeNode(2**31 - 1, None, TreeNode(2**31 - 1)),), (TreeNode(-1, TreeNode(-2)),)]


def big(rng):
    values = list(range(1 << 17))
    def build(lo, hi):
        if lo > hi:
            return None
        mid = (lo + hi) // 2
        return TreeNode(values[mid], build(lo, mid - 1), build(mid + 1, hi))
    return (build(0, len(values) - 1),)


def big_check(args, got):
    """Built from sorted values, so it is a valid search tree."""
    return strict_equal(got, True)
