# Valid Parentheses

[LeetCode 20](https://leetcode.com/problems/valid-parentheses/) | Stacks

**The problem.** A string holds only round, square and curly brackets. Decide whether every opener is closed by the matching kind, in the right order.

**Signature here.** `solve(s) -> bool`

**The shape to notice.** The most recent unclosed opener is the only one that can close next. Last in, first out means a stack.

**The idea.** Push each opener. Each closer must match the top of the stack, which it pops. At the end the stack must be empty.

**Complexity.** O(n) time and O(n) space. The slow machine can take O(n^2).

**How an AI answer to this would be checked.** Compare the yes or no against slow's, which uses a different method: it deletes matched neighbours until nothing changes. Half the generated strings are valid by construction, so an answer cannot pass by always saying no. Run it with `python3 check.py valid-parentheses --answer your_file.py`.

## Hunt the bugs first

`wrong.py` holds two wrong answers. Run `python3 check.py valid-parentheses`, read the smallest failing input for each, and work out why before you open these.

<details>
<summary>The gut answer</summary>

Equal counts ignore order. A closer before its opener, or two kinds crossing each other, still has equal counts.

</details>

<details>
<summary>The planted bug</summary>

`planted` is `fast.py` with one line changed. It has `return True` where the correct line is `return not stack`. Every closer that appears is checked, so strings with leftover openers are the only ones that get through. Anything ending with an unclosed opener passes.

</details>
