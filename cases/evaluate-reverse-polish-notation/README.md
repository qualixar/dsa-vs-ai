# Evaluate Reverse Polish Notation

[LeetCode 150](https://leetcode.com/problems/evaluate-reverse-polish-notation/) | Stacks

**The problem.** Work out the value of an expression written in postfix order, where each operator follows its two operands. Division rounds toward zero.

**Signature here.** `solve(items) -> int`

**The shape to notice.** An operator always applies to the two most recent results. Most recent first means a stack.

**The idea.** Push numbers. On an operator, pop two values, apply it and push the result. The first value popped is the right operand.

**Complexity.** O(n) time and O(n) space. The slow machine is O(n^2).

**How an AI answer to this would be checked.** Compare the value against slow's, which rewrites the list instead of using a stack. Generated expressions include negative numbers, because negative division is where this one goes wrong. Run it with `python3 check.py evaluate-reverse-polish-notation --answer your_file.py`.

## Hunt the bugs first

`wrong.py` holds two wrong answers. Run `python3 check.py evaluate-reverse-polish-notation`, read the smallest failing input for each, and work out why before you open these.

<details>
<summary>The gut answer</summary>

Python's `//` rounds down, not toward zero. The two agree on positive results and differ by one on negative ones, so tests with only positive numbers pass.

</details>

<details>
<summary>The planted bug</summary>

`planted` is `fast.py` with one line changed. It has `stack.append(b - a)` where the correct line is `stack.append(a - b)`. The first value popped is the right operand. This subtracts in the wrong order, which only matters when the two values differ.

</details>
