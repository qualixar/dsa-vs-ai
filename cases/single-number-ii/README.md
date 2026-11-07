# Single Number II

[LeetCode 137](https://leetcode.com/problems/single-number-ii/) | Bit tricks

**The problem.** Every value in a list of 32-bit integers appears exactly three times, except one that appears once. Find that one with constant extra memory.

**Signature here.** `solve(nums) -> int`

**The shape to notice.** Look at one bit position at a time. Values that appear three times add a multiple of 3 to that position's count, so the remainder belongs to the single value.

**The idea.** For each of 32 bits, count how many numbers have it set and take the count modulo 3. Rebuild the answer from those remainders, then read bit 31 as the sign.

**Complexity.** O(32 n) time and O(1) space. The slow machine is O(n^2).

**How an AI answer to this would be checked.** Compare the value against slow's, then against a count of every value on the large input. Both ends of the 32-bit range are always tried and half the inputs use the full width, because a mask that is too narrow passes on small numbers. Python's integers have no fixed width, so the sign must be restored by hand. Run it with `python3 check.py single-number-ii --answer your_file.py`.

## Hunt the bugs first

`wrong.py` holds two wrong answers. Run `python3 check.py single-number-ii`, read the smallest failing input for each, and work out why before you open these.

<details>
<summary>The gut answer</summary>

XOR cancels pairs, not triples. Three copies of a value XOR to that value, so the result mixes all of them together.

</details>

<details>
<summary>The planted bug</summary>

`planted` is `fast.py` with one line changed. It has `if answer > 1 << 32:` where the correct line is `if answer >= 1 << 31:`. The check for the sign bit can never be true in 32 bits, so a negative answer comes back as a large positive number. All positive inputs still pass.

</details>
