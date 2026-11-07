# Merge Intervals

[LeetCode 56](https://leetcode.com/problems/merge-intervals/) | Intervals

**The problem.** Given a list of closed intervals, combine any that overlap or touch and return the combined intervals in order.

**Signature here.** `solve(intervals) -> list of [start, end], sorted`

**The shape to notice.** After sorting by start, an interval can only touch the most recent merged one. Everything earlier is finished.

**The idea.** Sort, then sweep. If the next interval starts inside the last merged one, extend the end. Otherwise start a new merged interval.

**Complexity.** O(n log n) time and O(n) space. The slow machine is at least O(n^3).

**How an AI answer to this would be checked.** Compare the sorted list against slow's, which merges pairs until nothing changes and never sorts by start. Shared endpoints and intervals inside other intervals come up often at these sizes. Run it with `python3 check.py merge-intervals --answer your_file.py`.

## Hunt the bugs first

`wrong.py` holds two wrong answers. Run `python3 check.py merge-intervals`, read the smallest failing input for each, and work out why before you open these.

<details>
<summary>The gut answer</summary>

Without sorting, a later interval can bridge two earlier ones that were already separated, and this walk never goes back to join them.

</details>

<details>
<summary>The planted bug</summary>

`planted` is `fast.py` with one line changed. It has `out[-1][1] = end` where the correct line is `out[-1][1] = max(out[-1][1], end)`. Taking the new end assumes it is the larger one. An interval sitting inside the previous one shrinks the merged end.

</details>
