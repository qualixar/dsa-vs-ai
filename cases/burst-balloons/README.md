# Burst Balloons

[LeetCode 312](https://leetcode.com/problems/burst-balloons/) | DP: intervals

**The problem.** Balloons in a row carry numbers. Bursting one pays the product of its number and its two current neighbours, with 1 used beyond the ends. Neighbours close up afterward. Find the most you can collect by bursting them all.

**Signature here.** `solve(nums) -> int`

**The shape to notice.** Bursting first makes neighbours change, which is hard to track. Thinking about which balloon goes last inside a range makes the two sides independent.

**The idea.** For each range between two fixed walls, try each balloon as the last one to burst there. It pays its value times the two walls, plus the best of the two ranges on either side. Fill the table from narrow ranges to wide ones.

**Complexity.** O(n^3) time and O(n^2) space. The slow machine tries up to n! orders.

**How an AI answer to this would be checked.** Compare the total against slow's, which tries every order. Sizes stay small for that reason, and zeros are included since they punish simple rules. Run it with `python3 check.py burst-balloons --answer your_file.py`.

## Hunt the bugs first

`wrong.py` holds two wrong answers. Run `python3 check.py burst-balloons`, read the smallest failing input for each, and work out why before you open these.

<details>
<summary>The gut answer</summary>

Getting small numbers out of the way feels sensible, and it often gets close. But a small balloon can be worth keeping as a neighbour, or a large one worth keeping for the end, and this rule cannot see either.

</details>

<details>
<summary>The planted bug</summary>

`planted` is `fast.py` with one line changed. It has `gain = vals[last - 1] * vals[last] * vals[last + 1] + best[left][last] + best[last][right]` where the correct line is `gain = vals[left] * vals[last] * vals[right] + best[left][last] + best[last][right]`. The last balloon in a range sits between the range's walls at that moment, not its original neighbours. Using the original neighbours mixes up "first to burst" and "last to burst".

</details>
