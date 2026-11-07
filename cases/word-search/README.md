# Word Search

[LeetCode 79](https://leetcode.com/problems/word-search/) | Backtracking

**The problem.** A grid holds letters. Decide whether a word can be spelled by moving between cells that share an edge, using no cell twice.

**Signature here.** `solve(board, word) -> bool`

**The shape to notice.** A search over paths where each choice can be undone. Marking a cell on the way in and restoring it on the way out is the whole pattern.

**The idea.** From each cell, try to match the word one letter at a time. Mark the cell so the path cannot return to it, recurse in four directions, and restore the cell before returning.

**Complexity.** O(rows * cols * 3^L) time in the worst case for a word of length L, and O(L) stack. The slow machine explores every path of length L with no early stop on a wrong letter.

**How an AI answer to this would be checked.** Compare the yes or no against slow's. A two-letter alphabet makes dead ends common, which is what exposes a search that does not undo its marks. Run it with `python3 check.py word-search --answer your_file.py`.

## Hunt the bugs first

`wrong.py` holds two wrong answers. Run `python3 check.py word-search`, read the smallest failing input for each, and work out why before you open these.

<details>
<summary>The gut answer</summary>

Having the letters is not enough. They have to be next to each other in the right order, and this answer never looks at where they are.

</details>

<details>
<summary>The planted bug</summary>

`planted` is `fast.py` with one line changed. It has `pass` where the correct line is `board[r][c] = letter`. The mark is never removed, so a failed branch leaves its cells blocked for every later attempt. A word that needs a cell a dead end already touched gets reported as missing.

</details>
