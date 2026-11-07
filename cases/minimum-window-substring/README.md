# Minimum Window Substring

[LeetCode 76](https://leetcode.com/problems/minimum-window-substring/) | Sliding window

**The problem.** Find the shortest contiguous stretch of string `s` that contains every character of `t`, counting repeats. Return an empty string if there is none.

**Signature here.** `solve(s, t) -> str`

**The shape to notice.** A window that grows until it is good enough, then shrinks while it stays good enough. Counts stand in for repeated scanning.

**The idea.** Keep a counter of what is still needed and a number for how many characters are missing. Grow on the right until nothing is missing, then trim from the left and record where the shortest valid window starts. Slice the string once at the end, because copying each candidate would make this quadratic.

**Complexity.** O(len(s) + len(t)) time and O(size of the alphabet) space. The slow machine is at least O(n^2) stretches, each counted.

**How an AI answer to this would be checked.** Several windows of the same length can be valid, so the check tests the length against slow's and then confirms the window is a real stretch of `s` that covers `t`. Run it with `python3 check.py minimum-window-substring --answer your_file.py`.

## Hunt the bugs first

`wrong.py` holds two wrong answers. Run `python3 check.py minimum-window-substring`, read the smallest failing input for each, and work out why before you open these.

<details>
<summary>The gut answer</summary>

The first window that covers `t` can be trimmed but it may not be the shortest. A better window can start much later, and this answer never looks.

</details>

<details>
<summary>The planted bug</summary>

`planted` is `fast.py` with one line changed. It has `if need[s[lo]] >= 0:` where the correct line is `if need[s[lo]] > 0:`. A count that returns to exactly zero means the window still has just enough of that character. Treating zero as missing ends the shrink one step too soon, so valid shorter windows are lost and spare letters get counted as gaps.

</details>
