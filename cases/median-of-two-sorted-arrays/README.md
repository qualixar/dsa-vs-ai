# Median of Two Sorted Arrays

[LeetCode 4](https://leetcode.com/problems/median-of-two-sorted-arrays/) | Binary search

**The problem.** Two lists, each sorted, hold numbers. Find the median of all the numbers together in logarithmic time, without merging them.

**Signature here.** `solve(a, b) -> float`

**The shape to notice.** A median is a split into a low half and a high half. If you know how many items the low half takes from one list, the other list's share is forced.

**The idea.** Binary search the split point of the shorter list. A split is right when the largest low item on each side is no bigger than the smallest high item on the other side.

**Complexity.** O(log min(m, n)) time and O(1) space. The slow machine is O((m + n) log(m + n)).

**How an AI answer to this would be checked.** Compare the float against slow's on pairs of every size split, including one empty list. The large input finishes either way, so read the loop to confirm the logarithmic part. Run it with `python3 check.py median-of-two-sorted-arrays --answer your_file.py`.

## Hunt the bugs first

`wrong.py` holds two wrong answers. Run `python3 check.py median-of-two-sorted-arrays`, read the smallest failing input for each, and work out why before you open these.

<details>
<summary>The gut answer</summary>

The median of medians gives the right answer only when the two lists are balanced in the right way. A list with one huge value and a list with many small ones pulls the average far from the real middle.

</details>

<details>
<summary>The planted bug</summary>

`planted` is `fast.py` with one line changed. It has `half = (m + n) // 2` where the correct line is `half = (m + n + 1) // 2`. The extra `+ 1` is what gives the low half the middle item when the total is odd. Without it, odd totals report the wrong element.

</details>
