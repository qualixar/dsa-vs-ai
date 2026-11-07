# Validate Binary Search Tree

[LeetCode 98](https://leetcode.com/problems/validate-binary-search-tree/) | Trees

**The problem.** Decide whether a binary tree is a strict search tree: at every node, everything in the left part is smaller and everything in the right part is larger.

**Signature here.** `solve(root) -> bool (see cases/structures.py)`

**The shape to notice.** The rule covers whole subtrees, not just children. Each node inherits a range from all its ancestors.

**The idea.** Pass a low and high bound down the recursion. Going left lowers the high bound to this node's value. Going right raises the low bound.

**Complexity.** O(n) time and O(h) stack for tree height h. The slow machine is O(n^2).

**How an AI answer to this would be checked.** Compare the yes or no against slow's, which tests the definition directly. The generator disturbs one value of a real search tree, because that is what makes a tree look right locally and fail globally. Both ends of the 32-bit range are always tried, which catches bounds that use those numbers as stand-ins for infinity. Run it with `python3 check.py validate-binary-search-tree --answer your_file.py`.

## Hunt the bugs first

`wrong.py` holds two wrong answers. Run `python3 check.py validate-binary-search-tree`, read the smallest failing input for each, and work out why before you open these.

<details>
<summary>The gut answer</summary>

Checking only direct children misses a value deep in the left part that is larger than a distant ancestor. Each parent and child pair looks fine.

</details>

<details>
<summary>The planted bug</summary>

`planted` is `fast.py` with one line changed. It has `if not low <= node.val <= high:` where the correct line is `if not low < node.val < high:`. Allowing equality accepts repeated values on a path. The definition here is strict, so a tree holding the same value twice along a path is not valid.

</details>
