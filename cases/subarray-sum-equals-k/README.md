# Subarray Sum Equals K

[LeetCode 560](https://leetcode.com/problems/subarray-sum-equals-k/) | Arrays and hashing

**The problem.** Count the contiguous stretches of a list whose entries add up to exactly k. The entries can be negative.

**Signature here.** `solve(nums, k) -> int`

**The shape to notice.** The sum of a stretch is the difference of two running totals. A question about stretches becomes a question about pairs of running totals.

**The idea.** Keep a running total and a count of each total seen so far. A stretch ending here sums to k once for every earlier total equal to `total - k`.

**Complexity.** O(n) time and O(n) space. The slow machine is O(n^3) as written.

**How an AI answer to this would be checked.** Compare the count against slow's on inputs that include negatives and zeros. An answer tested only on positive numbers can pass here by luck, which is why the generator never stays positive. Run it with `python3 check.py subarray-sum-equals-k --answer your_file.py`.

## Hunt the bugs first

`wrong.py` holds two wrong answers. Run `python3 check.py subarray-sum-equals-k`, read the smallest failing input for each, and work out why before you open these.

<details>
<summary>The gut answer</summary>

A sliding window relies on the sum growing as the window grows, which only holds when every entry is positive. A negative number breaks that, so stretches get skipped.

</details>

<details>
<summary>The planted bug</summary>

`planted` is `fast.py` with one line changed. It has `counts = {}` where the correct line is `counts = {0: 1}`. The empty prefix has total 0, and it has to be counted. Without it, every stretch that starts at the first position is missed.

</details>
