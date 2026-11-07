"""Two wrong answers to hunt. Run the check first; README.md explains both behind a fold."""


def gut(head):
    """Remember every value visited."""
    seen = set()
    while head is not None:
        if head.val in seen:
            return True
        seen.add(head.val)
        head = head.next
    return False


# A copy of fast.py with exactly one line changed. Find it.
def planted(head):
    slow = fast = head
    while fast and fast.next:
        slow = slow.next
        fast = fast.next
        if slow is fast:
            return True
    return False
