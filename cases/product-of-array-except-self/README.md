# Product of Array Except Self

[LeetCode 238](https://leetcode.com/problems/product-of-array-except-self/) | Arrays and hashing

**The problem.** For each position in a list of whole numbers, give the product of all the other entries. The classic form of this question also forbids division.

**Signature here.** `solve(nums) -> list of int`

**The shape to notice.** Each answer splits into two parts: everything to the left and everything to the right. Both parts can be built up in one pass.

**The idea.** One pass left to right stores the product of everything before each position. A second pass right to left multiplies in the product of everything after it.

**Complexity.** O(n) time and O(1) extra space beyond the answer. The slow machine is O(n^2).

**How an AI answer to this would be checked.** Compare the whole list against slow's on small inputs that include zeros and negatives, because zeros are where this question hides its traps. Run it with `python3 check.py product-of-array-except-self --answer your_file.py`.

## Hunt the bugs first

`wrong.py` holds two wrong answers. Run `python3 check.py product-of-array-except-self`, read the smallest failing input for each, and work out why before you open these.

<details>
<summary>The gut answer</summary>

Dividing the total by each number looks fine until a zero appears. With exactly one zero the total is zero, yet that zero's own slot should hold the product of all the others. Giving it a zero is wrong.

</details>

<details>
<summary>The planted bug</summary>

`planted` is `fast.py` with one line changed. It has `for i in range(len(nums) - 1, 0, -1):` where the correct line is `for i in range(len(nums) - 1, -1, -1):`. Stopping the backward pass at index 1 means position 0 never receives the product of what follows it.

</details>
