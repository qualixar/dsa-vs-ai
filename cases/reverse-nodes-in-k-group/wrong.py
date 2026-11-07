"""Two wrong answers to hunt. Run the check first; README.md explains both behind a fold."""
from structures import ListNode, linked, values_of


def gut(head, k):
    """Reverse every block of k, including the short block at the end."""
    values = values_of(head)
    out = []
    for i in range(0, len(values), k):
        out += values[i:i + k][::-1]
    return linked(out)


# A copy of fast.py with exactly one line changed. Find it.
def planted(head, k):
    dummy = ListNode(0, head)
    group_prev = dummy
    while True:
        last = group_prev
        for _ in range(k):
            last = last.next
            if last is None:
                return dummy.next
        group_next = last.next
        prev, node = None, group_prev.next
        while node is not group_next:
            node.next, prev, node = prev, node, node.next
        new_tail = group_prev.next
        group_prev.next = last
        group_prev = new_tail
