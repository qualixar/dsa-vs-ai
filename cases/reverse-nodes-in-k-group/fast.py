from structures import ListNode


def solve(head, k):
    dummy = ListNode(0, head)
    group_prev = dummy
    while True:
        last = group_prev
        for _ in range(k):
            last = last.next
            if last is None:
                return dummy.next
        group_next = last.next
        prev, node = group_next, group_prev.next
        while node is not group_next:
            node.next, prev, node = prev, node, node.next
        new_tail = group_prev.next
        group_prev.next = last
        group_prev = new_tail
