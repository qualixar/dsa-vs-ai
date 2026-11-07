from heapq import heapify, heappop, heappush
from structures import ListNode


def solve(lists):
    heap = [(node.val, i, node) for i, node in enumerate(lists) if node]
    heapify(heap)
    dummy = tail = ListNode(0)
    while heap:
        val, i, node = heappop(heap)
        tail.next = node
        tail = node
        if node.next:
            heappush(heap, (node.next.val, i, node.next))
    return dummy.next
