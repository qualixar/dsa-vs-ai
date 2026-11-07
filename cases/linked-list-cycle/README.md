# Linked List Cycle

[LeetCode 141](https://leetcode.com/problems/linked-list-cycle/) | Linked structures

**The problem.** Decide whether a linked list loops back on itself, ideally using constant extra memory.

**Signature here.** `solve(head) -> bool`

**The shape to notice.** Two runners at different speeds on a circular track must meet. On a straight track the fast one reaches the end.

**The idea.** Move one pointer by one step and another by two. If they ever land on the same node, there is a cycle. If the fast one runs out of list, there is not.

**Complexity.** O(n) time and O(1) space. The slow machine is O(n) time and O(n) space.

**How an AI answer to this would be checked.** Compare the yes or no against slow's. Values repeat often in the generated lists, so comparing values instead of node identity gets caught. Run it with `python3 check.py linked-list-cycle --answer your_file.py`.

## Hunt the bugs first

`wrong.py` holds two wrong answers. Run `python3 check.py linked-list-cycle`, read the smallest failing input for each, and work out why before you open these.

<details>
<summary>The gut answer</summary>

A repeated value is not a repeated node. Two different nodes can hold the same number, so this reports loops that are not there.

</details>

<details>
<summary>The planted bug</summary>

`planted` is `fast.py` with one line changed. It has `fast = fast.next` where the correct line is `fast = fast.next.next`. With both pointers moving one step, they stay together from the first move, so the very first comparison says yes. Any list with two nodes or more is called a cycle.

</details>
