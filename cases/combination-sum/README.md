# Combination Sum

[LeetCode 39](https://leetcode.com/problems/combination-sum/) | Backtracking

**The problem.** Given distinct positive numbers and a target, list every multiset of those numbers that adds up to the target. Each number may be used any number of times.

**Signature here.** `solve(candidates, target) -> list of lists`

**The shape to notice.** A choice tree where you must not generate the same multiset twice. A rule that picks only from the current position onward removes the repeats without any set.

**The idea.** Recurse with a start index. Each call chooses from that index on, and passes the same index down, so a number can repeat and earlier numbers cannot come back.

**Complexity.** Exponential in the worst case, with time proportional to the combinations found times their length. The slow machine tries the product of all possible counts.

**How an AI answer to this would be checked.** Order inside and between combinations does not matter, so both answers are sorted first. A repeated combination counts as wrong. Run it with `python3 check.py combination-sum --answer your_file.py`.

## Hunt the bugs first

`wrong.py` holds two wrong answers. Run `python3 check.py combination-sum`, read the smallest failing input for each, and work out why before you open these.

<details>
<summary>The gut answer</summary>

Trying every candidate at every step generates each multiset once per ordering, so 2 + 3 and 3 + 2 both appear. It finds the right sets, then reports some of them again.

</details>

<details>
<summary>The planted bug</summary>

`planted` is `fast.py` with one line changed. It has `walk(i + 1, left - candidates[i])` where the correct line is `walk(i, left - candidates[i])`. Passing `i + 1` moves past the number just used, so no number can repeat. Combinations with a repeated number are lost.

</details>
