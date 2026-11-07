# Largest Rectangle in Histogram

[LeetCode 84](https://leetcode.com/problems/largest-rectangle-in-histogram/) | Stacks

**The problem.** Bars of width 1 stand side by side. Find the area of the largest rectangle that fits under them.

**Signature here.** `solve(heights) -> int`

**The shape to notice.** Each bar could be the shortest bar of some rectangle. That rectangle reaches to the nearest shorter bar on each side, and a monotonic stack finds those neighbours.

**The idea.** Keep a stack of bars with rising heights. When a shorter bar arrives, each taller bar on the stack has found its right limit, and the bar beneath it on the stack is its left limit. A height 0 added at the end empties the stack.

**Complexity.** O(n) time and O(n) space, since each bar is pushed and popped once. The slow machine is O(n^2).

**How an AI answer to this would be checked.** Compare the area against slow's on short rows with small heights, where ties between equal bars come up often. Run it with `python3 check.py largest-rectangle-in-histogram --answer your_file.py`.

## Hunt the bugs first

`wrong.py` holds two wrong answers. Run `python3 check.py largest-rectangle-in-histogram`, read the smallest failing input for each, and work out why before you open these.

<details>
<summary>The gut answer</summary>

The best rectangle is often neither extreme. It usually spans part of the row at a middle height, which this answer never considers.

</details>

<details>
<summary>The planted bug</summary>

`planted` is `fast.py` with one line changed. It has `left = stack[-1] if stack else 0` where the correct line is `left = stack[-1] if stack else -1`. When the stack is empty, the rectangle reaches all the way to the left edge. Using 0 instead of -1 loses one bar of width from those rectangles.

</details>
