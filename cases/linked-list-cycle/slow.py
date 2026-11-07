def solve(head):
    """Remember every node visited."""
    visited = set()
    while head is not None:
        if id(head) in visited:
            return True
        visited.add(id(head))
        head = head.next
    return False
