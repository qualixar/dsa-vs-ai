# Binary Tree Maximum Path Sum

[LeetCode 124](https://leetcode.com/problems/binary-tree-maximum-path-sum/) | Trees

**The problem.** A path in a binary tree is a chain of connected nodes with no repeats, and it can bend once at its highest node. Node values can be negative. Find the largest total any path can have.

**Signature here.** `solve(root) -> int (see cases/structures.py)`

**The shape to notice.** Two answers per node: the best path bending here, which can use both sides, and the best path going up to the parent, which can use only one.

**The idea.** Recurse, returning the best one-sided gain. Treat a negative gain as zero, since you can refuse a side. At each node, record the bend total as a candidate for the overall answer.

**Complexity.** O(n) time and O(h) stack. The slow machine is O(n^2).

**How an AI answer to this would be checked.** Compare the total against slow's, which walks from every node in every direction. Trees of all negative values are generated too, since the path must hold at least one node. Run it with `python3 check.py binary-tree-maximum-path-sum --answer your_file.py`.

## Hunt the bugs first

`wrong.py` holds two wrong answers. Run `python3 check.py binary-tree-maximum-path-sum`, read the smallest failing input for each, and work out why before you open these.

<details>
<summary>The gut answer</summary>

A path can go up one side and down the other. Looking only at downward paths misses the bend, so a parent with two good children is undercounted.

</details>

<details>
<summary>The planted bug</summary>

`planted` is `fast.py` with one line changed. It has `left = gain(node.left)` where the correct line is `left = max(gain(node.left), 0)`. A side with a negative total should be refused. Keeping it forces the path to carry a loss, even though stopping at this node would do better.

</details>
