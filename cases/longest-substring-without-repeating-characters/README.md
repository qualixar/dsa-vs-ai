# Longest Substring Without Repeating Characters

[LeetCode 3](https://leetcode.com/problems/longest-substring-without-repeating-characters/) | Sliding window

**The problem.** Given a string, find the length of the longest contiguous stretch in which no character appears twice.

**Signature here.** `solve(s) -> int`

**The shape to notice.** A window that only ever moves right, with a rule for when its left edge has to jump.

**The idea.** Remember where each character was last seen. When the current character is already inside the window, move the left edge just past its last position. The left edge never moves back.

**Complexity.** O(n) time and O(size of the alphabet) space. The slow machine is O(n^3).

**How an AI answer to this would be checked.** Compare the length against slow's on strings over a tiny alphabet, because a tiny alphabet is what forces repeats and re-entry into old characters. Run it with `python3 check.py longest-substring-without-repeating-characters --answer your_file.py`.

## Hunt the bugs first

`wrong.py` holds two wrong answers. Run `python3 check.py longest-substring-without-repeating-characters`, read the smallest failing input for each, and work out why before you open these.

<details>
<summary>The gut answer</summary>

Starting over from the repeated letter throws away characters that were still valid. After the repeat, part of the old run could have stayed in the window.

</details>

<details>
<summary>The planted bug</summary>

`planted` is `fast.py` with one line changed. It has `start = last[c] + 1` where the correct line is `start = max(start, last[c] + 1)`. Without the `max`, the left edge can jump backward to a character that is already outside the window, which brings a repeat back in. It only shows when an older repeat comes after a newer one.

</details>
