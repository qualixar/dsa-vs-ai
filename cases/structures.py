"""Linked lists and binary trees shared by the cases. Both print as plain lists, so a failing input is readable."""


class ListNode:
    def __init__(self, val, next=None):
        self.val = val
        self.next = next

    def __repr__(self):
        seen = {}
        values = []
        node = self
        while node is not None and id(node) not in seen:
            seen[id(node)] = len(values)
            values.append(repr(node.val))
            node = node.next
        tail = "" if node is None else f" then back to index {seen[id(node)]}"
        return "[" + ", ".join(values) + tail + "]"


def linked(values, loop_to=None):
    """Build a list. With loop_to, the last node points back at that index, making a cycle."""
    nodes = [ListNode(v) for v in values]
    for a, b in zip(nodes, nodes[1:]):
        a.next = b
    if loop_to is not None and nodes:
        nodes[-1].next = nodes[loop_to]
    return nodes[0] if nodes else None


def values_of(head):
    """Values of a list. A loop raises ValueError, and anything that is not a list of nodes raises AttributeError."""
    out = []
    seen = set()
    while head is not None:
        if id(head) in seen:
            raise ValueError("the list loops back on itself")
        seen.add(id(head))
        out.append(head.val)
        head = head.next
    return out


class TreeNode:
    def __init__(self, val, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right

    def __repr__(self):
        rows = []
        level = [self]
        while level:
            rows.extend(repr(n.val) if n else "None" for n in level)
            level = [c for n in level if n for c in (n.left, n.right)]
        while rows and rows[-1] == "None":
            rows.pop()
        return "[" + ", ".join(rows) + "]"


def random_tree(rng, size, value):
    """A random binary tree shape of `size` nodes. `value()` supplies each node's value."""
    if size <= 0:
        return None
    root = TreeNode(value())
    nodes = [root]
    while len(nodes) < size:
        parent = rng.choice(nodes)
        side = rng.choice(("left", "right"))
        if getattr(parent, side) is None:
            child = TreeNode(value())
            setattr(parent, side, child)
            nodes.append(child)
    return root
