# Non-overlapping Intervals

[LeetCode 435](https://leetcode.com/problems/non-overlapping-intervals/) | Greedy

**The problem.** Remove as few intervals as possible so that the rest do not overlap. Intervals that only touch at an endpoint are fine together.

**Signature here.** `solve(intervals) -> int, the number removed`

**The shape to notice.** Keeping the most intervals is the mirror of removing the fewest. The interval that ends first leaves the most room, and an exchange argument shows that choosing it is never worse.

**The idea.** Sort by end time. Keep each interval that starts at or after the end of the last kept one.

**Complexity.** O(n log n) time and O(n) space for the sorted copy. The slow machine tries up to 2^n subsets.

**How an AI answer to this would be checked.** Compare the count against slow's, which tries every subset. Sizes stay small because of that, and small sizes still force long intervals covering short ones. Run it with `python3 check.py non-overlapping-intervals --answer your_file.py`.

## Hunt the bugs first

`wrong.py` holds two wrong answers. Run `python3 check.py non-overlapping-intervals`, read the smallest failing input for each, and work out why before you open these.

<details>
<summary>The gut answer</summary>

Starting first says nothing about how much room an interval takes. A long interval that starts early can block several short ones, and this keeps it.

</details>

<details>
<summary>The planted bug</summary>

`planted` is `fast.py` with one line changed. It has `if start > last_end:` where the correct line is `if start >= last_end:`. Intervals that only touch are compatible, so the test has to allow equality. With `>`, touching intervals count as overlapping and too many are removed.

</details>
