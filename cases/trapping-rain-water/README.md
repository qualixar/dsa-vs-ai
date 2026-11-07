# Trapping Rain Water

[LeetCode 42](https://leetcode.com/problems/trapping-rain-water/) | Two pointers

**The problem.** A row of bars of given heights stands in the rain. Work out how many unit squares of water stay trapped between them.

**Signature here.** `solve(heights) -> int`

**The shape to notice.** The water over one bar depends only on the tallest bar to its left and the tallest bar to its right. You do not need both exactly, only the smaller one.

**The idea.** Move two pointers inward from the ends, always handling the lower side. Whatever is higher on the far side is already tall enough, so the near side's maximum decides the level for that bar.

**Complexity.** O(n) time and O(1) space. The slow machine is O(n^2).

**How an AI answer to this would be checked.** Compare the total against slow's on small rows. Round 1 of this repository used this same problem as its control, with a separate grader under `rounds/round1/`. This case is for practice and is not part of that result. Run it with `python3 check.py trapping-rain-water --answer your_file.py`.

## Hunt the bugs first

`wrong.py` holds two wrong answers. Run `python3 check.py trapping-rain-water`, read the smallest failing input for each, and work out why before you open these.

<details>
<summary>The gut answer</summary>

Filling between neighbouring peaks misses water standing above a small peak. A short bar in the middle of a basin counts as a peak, so the basin is measured at the short bar's height instead of the rim's.

</details>

<details>
<summary>The planted bug</summary>

`planted` is `fast.py` with one line changed. It has `while lo < hi - 1:` where the correct line is `while lo < hi:`. The loop stops one bar early. When two pointers are next to each other, one bar still has to be handled, and that bar can hold water.

</details>
