# Reverse Nodes in k-Group

[LeetCode 25](https://leetcode.com/problems/reverse-nodes-in-k-group/) | Linked structures

**The problem.** Reverse a linked list in consecutive blocks of k nodes. A short block left over at the end stays as it is.

**Signature here.** `solve(head, k) -> head of a linked list (see cases/structures.py)`

**The shape to notice.** Four pointers around a block: the node before it, its first node, its last node and the node after it. Everything is relinking those four.

**The idea.** Scout k nodes ahead to confirm a full block exists. Reverse the block with its tail pointing at whatever follows, connect the node before it to the block's new front, then step forward to the block's new tail.

**Complexity.** O(n) time and O(1) space. The slow machine is O(n) time and O(n) space. Here slow is not slower, only simpler, and that is what makes it a fair key.

**How an AI answer to this would be checked.** Both results become plain lists of values and are compared. Lists shorter than k, exact multiples of k and k of 1 are all generated. Run it with `python3 check.py reverse-nodes-in-k-group --answer your_file.py`.

## Hunt the bugs first

`wrong.py` holds two wrong answers. Run `python3 check.py reverse-nodes-in-k-group`, read the smallest failing input for each, and work out why before you open these.

<details>
<summary>The gut answer</summary>

The statement says leftovers stay put, and a quick reading misses that. The answer is right when the length is a multiple of k, so tests that use only such lengths pass.

</details>

<details>
<summary>The planted bug</summary>

`planted` is `fast.py` with one line changed. It has `prev, node = None, group_prev.next` where the correct line is `prev, node = group_next, group_prev.next`. The reversed block should point on to what follows it. Starting from `None` cuts the list after the first block, so everything later is lost. A list of k nodes or fewer looks fine.

</details>
