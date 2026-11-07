# Merge k Sorted Lists

[LeetCode 23](https://leetcode.com/problems/merge-k-sorted-lists/) | Heaps

**The problem.** Several linked lists are each sorted. Join them into one sorted linked list.

**Signature here.** `solve(lists) -> head of a linked list (see cases/structures.py)`

**The shape to notice.** At any moment the next value is the smallest among the fronts of the lists. "Smallest of a changing few" is what a heap does.

**The idea.** Put each list's front in a min-heap. Pop the smallest, link it on, then push that node's successor. The list number in the tuple breaks ties so nodes are never compared.

**Complexity.** O(n log k) time and O(k) space for n nodes in k lists. The slow machine is O(n log n).

**How an AI answer to this would be checked.** The check turns both results into plain lists of values and compares those. It does not check that nodes were reused. Run it with `python3 check.py merge-k-sorted-lists --answer your_file.py`.

## Hunt the bugs first

`wrong.py` holds two wrong answers. Run `python3 check.py merge-k-sorted-lists`, read the smallest failing input for each, and work out why before you open these.

<details>
<summary>The gut answer</summary>

Joining lists by their first value only works when their ranges do not overlap. Once they interleave, the result is not sorted.

</details>

<details>
<summary>The planted bug</summary>

`planted` is `fast.py` with one line changed. It has `heappush(heap, (node.val, i, node.next))` where the correct line is `heappush(heap, (node.next.val, i, node.next))`. The successor goes into the heap under its predecessor's value, so it comes out earlier than it should. A later list's smaller front can end up behind a larger value.

</details>
