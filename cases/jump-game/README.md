# Jump Game

[LeetCode 55](https://leetcode.com/problems/jump-game/) | Greedy

**The problem.** Each entry says the longest jump allowed from that position. Starting at the first position, decide whether the last one can be reached.

**Signature here.** `solve(nums) -> bool`

**The shape to notice.** Only the farthest position you can get to matters, not how you get there.

**The idea.** Scan left to right, tracking the farthest reachable index. If the scan arrives at a position beyond that, the position cannot be reached and neither can anything after it.

**Complexity.** O(n) time and O(1) space. The slow machine can take O(n * m) for jump size m.

**How an AI answer to this would be checked.** Compare the yes or no against slow's, which explores every jump. Zeros are common in the generated lists, because zeros are the only way to get stuck. Run it with `python3 check.py jump-game --answer your_file.py`.

## Hunt the bugs first

`wrong.py` holds two wrong answers. Run `python3 check.py jump-game`, read the smallest failing input for each, and work out why before you open these.

<details>
<summary>The gut answer</summary>

The longest jump can land on a zero while a shorter jump would have landed somewhere useful. The problem says the jump is at most that long, not exactly that long.

</details>

<details>
<summary>The planted bug</summary>

`planted` is `fast.py` with one line changed. It has `reach = i + jump` where the correct line is `reach = max(reach, i + jump)`. This forgets longer jumps seen earlier. A long jump followed by a short one sets the reach back, so a position that can be reached gets reported as blocked.

</details>
