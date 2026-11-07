# Partition Equal Subset Sum

[LeetCode 416](https://leetcode.com/problems/partition-equal-subset-sum/) | DP: 2D

**The problem.** Decide whether a list of positive numbers can be split into two groups with equal sums.

**Signature here.** `solve(nums) -> bool`

**The shape to notice.** It is 0/1 knapsack in disguise: can some subset reach half the total? The table is items by sums, and it folds into one row.

**The idea.** Mark which sums are reachable. For each number, update the row from high to low, so the number can be used at most once. Going low to high would let it count many times.

**Complexity.** O(n * total) time and O(total) space. The slow machine tries 2^n subsets.

**How an AI answer to this would be checked.** Compare the yes or no against slow's, which tries every subset. Half of all inputs have an odd total and are easy, so the failure counts here are lower than in most cases. Run it with `python3 check.py partition-equal-subset-sum --answer your_file.py`.

## Hunt the bugs first

`wrong.py` holds two wrong answers. Run `python3 check.py partition-equal-subset-sum`, read the smallest failing input for each, and work out why before you open these.

<details>
<summary>The gut answer</summary>

Adding to the lighter side is a good approximation, and it is often right, but it is not exact. Splits that need a specific grouping get missed.

</details>

<details>
<summary>The planted bug</summary>

`planted` is `fast.py` with one line changed. It has `for s in range(x, target + 1):` where the correct line is `for s in range(target, x - 1, -1):`. Updating low to high means a sum made with this number can be used again by the same number in the same pass. That is unbounded knapsack, so one number gets counted several times.

</details>
