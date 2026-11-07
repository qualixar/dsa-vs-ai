"""Two wrong answers to hunt. Run the check first; README.md explains both behind a fold."""
from heapq import heapify, heappop, heappush
from structures import ListNode, linked, values_of


def gut(lists):
    """Order the lists by their first value, then join them end to end."""
    joined = []
    for head in sorted((h for h in lists if h), key=lambda h: h.val):
        joined += values_of(head)
    return linked(joined)


# A copy of fast.py with exactly one line changed. Find it.
def planted(lists):
    heap = [(node.val, i, node) for i, node in enumerate(lists) if node]
    heapify(heap)
    dummy = tail = ListNode(0)
    while heap:
        val, i, node = heappop(heap)
        tail.next = node
        tail = node
        if node.next:
            heappush(heap, (node.val, i, node.next))
    return dummy.next
