# Counting Bits

[LeetCode 338](https://leetcode.com/problems/counting-bits/) | Bit tricks

**The problem.** For every number from 0 to n, report how many 1 bits it has.

**Signature here.** `solve(n) -> list of int`

**The shape to notice.** Each number's count relates to a smaller number you already have. `i & (i - 1)` clears the lowest set bit, so the count is one more than that smaller number's.

**The idea.** Build the list upward. For each i, add one to the count for `i & (i - 1)`.

**Complexity.** O(n) time and O(n) space. The slow machine is O(n log n), and it is a fair key because it does the counting directly from the definition.

**How an AI answer to this would be checked.** Compare the list against slow's. Here the input is a single number, so the runner tries n from 0 to 200 and reports 201 inputs. That covers each n once, not thousands of random draws. Run it with `python3 check.py counting-bits --answer your_file.py`.

## Hunt the bugs first

`wrong.py` holds two wrong answers. Run `python3 check.py counting-bits`, read the smallest failing input for each, and work out why before you open these.

<details>
<summary>The gut answer</summary>

It is right for the first few numbers and breaks at 4. Moving from 3 to 4 clears two 1 bits and sets one, which the rule cannot express.

</details>

<details>
<summary>The planted bug</summary>

`planted` is `fast.py` with one line changed. It has `bits[i] = bits[i >> 1] + 1` where the correct line is `bits[i] = bits[i & (i - 1)] + 1`. `i >> 1` removes the lowest bit whether it is 0 or 1, so this adds 1 even when nothing was removed. That is right for odd numbers and wrong for even ones. The correct shift-based form adds `i & 1`, not 1.

</details>
