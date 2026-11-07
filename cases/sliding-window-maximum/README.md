# Sliding Window Maximum

[LeetCode 239](https://leetcode.com/problems/sliding-window-maximum/) | Sliding window

**The problem.** Slide a window of width k across a list one step at a time. Report the largest value in the window at each position.

**Signature here.** `solve(nums, k) -> list of int`

**The shape to notice.** Once a newer number is at least as large, an older smaller number can never be the answer again. Candidates that can never win can be thrown away.

**The idea.** Keep a deque of positions whose values decrease from front to back. A new number pushes out everything no larger than it. The front is the maximum, and it leaves once it falls outside the window.

**Complexity.** O(n) time and O(k) space, since each position enters and leaves once. The slow machine is O(nk).

**How an AI answer to this would be checked.** Compare the whole list against slow's, on widths from 1 up to the full list. Run it with `python3 check.py sliding-window-maximum --answer your_file.py`.

## Hunt the bugs first

`wrong.py` holds two wrong answers. Run `python3 check.py sliding-window-maximum`, read the smallest failing input for each, and work out why before you open these.

<details>
<summary>The gut answer</summary>

When the best number leaves the window, the next best is usually somewhere in the middle of the window. Taking the newest number gives a value that may not be the maximum at all.

</details>

<details>
<summary>The planted bug</summary>

`planted` is `fast.py` with one line changed. It has `if window[0] < i - k:` where the correct line is `if window[0] <= i - k:`. The window test is off by one, so a number stays at the front for one step after it has left the window. It only shows when the old maximum is larger than everything now inside.

</details>
