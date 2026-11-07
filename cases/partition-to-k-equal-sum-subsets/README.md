# Partition to K Equal Sum Subsets

[LeetCode 698](https://leetcode.com/problems/partition-to-k-equal-sum-subsets/) | DP: bitmask

**The problem.** Decide whether a list of positive numbers can be split into k groups that all have the same sum.

**Signature here.** `solve(nums, k) -> bool`

**The shape to notice.** Which numbers have been used is all that matters, not the order they were used in. With few numbers, that fits in the bits of an integer.

**The idea.** For each subset, stored as a bitmask, record how full the current group would be if that subset can be arranged at all. Add a number only if it fits in the current group, and start a new group when one fills exactly.

**Complexity.** O(n * 2^n) time and O(2^n) space. The slow machine tries k^n assignments.

**How an AI answer to this would be checked.** Compare the yes or no against slow's, which tries every assignment. A total that does not divide by k is an easy no, so failures come from the inputs that pass that first test. Run it with `python3 check.py partition-to-k-equal-sum-subsets --answer your_file.py`.

## Hunt the bugs first

`wrong.py` holds two wrong answers. Run `python3 check.py partition-to-k-equal-sum-subsets`, read the smallest failing input for each, and work out why before you open these.

<details>
<summary>The gut answer</summary>

First fit decreasing is a good packing rule and usually works, but it is not exact. It can fill a group in a way that leaves the rest impossible, and it never goes back.

</details>

<details>
<summary>The planted bug</summary>

`planted` is `fast.py` with one line changed. It has `if not mask & bit:` where the correct line is `if not mask & bit and fill[mask] + nums[i] <= side:`. The bound is what keeps a group from overflowing. Without it a number can spill across a group boundary, and the modulo hides the overflow, so impossible splits get reported as possible.

</details>
