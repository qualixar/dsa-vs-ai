# Longest Increasing Subsequence

[LeetCode 300](https://leetcode.com/problems/longest-increasing-subsequence/) | DP: 1D

**The problem.** Find the length of the longest subsequence, not necessarily contiguous, whose values strictly increase.

**Signature here.** `solve(nums) -> int`

**The shape to notice.** For each length, only the smallest possible tail matters. Those smallest tails are always in increasing order, so you can binary search them.

**The idea.** `tails[i]` holds the smallest last value of any increasing subsequence of length i + 1. Each new number replaces the first tail that is at least as large, or extends the list.

**Complexity.** O(n log n) time and O(n) space. The slow machine tries up to 2^n subsequences.

**How an AI answer to this would be checked.** Compare the length against slow's. Values repeat often here, which separates strictly increasing from non-decreasing. Run it with `python3 check.py longest-increasing-subsequence --answer your_file.py`.

## Hunt the bugs first

`wrong.py` holds two wrong answers. Run `python3 check.py longest-increasing-subsequence`, read the smallest failing input for each, and work out why before you open these.

<details>
<summary>The gut answer</summary>

Taking every larger number commits to the first number and to each early choice. One large number early on blocks a longer run of smaller ones.

</details>

<details>
<summary>The planted bug</summary>

`planted` is `fast.py` with one line changed. It has `i = bisect.bisect_right(tails, x)` where the correct line is `i = bisect.bisect_left(tails, x)`. `bisect_right` steps past equal values, so a repeat extends the list as if it were an increase. That counts non-decreasing runs, not strictly increasing ones.

</details>
