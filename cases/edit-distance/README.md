# Edit Distance

[LeetCode 72](https://leetcode.com/problems/edit-distance/) | DP: 2D

**The problem.** Find the fewest single-letter inserts, deletes and replacements that turn one string into another.

**Signature here.** `solve(a, b) -> int`

**The shape to notice.** Two strings consumed from the front, and only the two positions matter. That gives a grid of subproblems with three moves between neighbours.

**The idea.** Cell (i, j) is the answer for the first i letters of `a` and first j letters of `b`. It comes from the cell above, the cell to the left or the diagonal, where the diagonal costs nothing on a letter match. One row of the grid is enough at a time.

**Complexity.** O(mn) time and O(n) space. The slow machine is exponential with no table.

**How an AI answer to this would be checked.** Compare the distance against slow's, which recurses over the three edits directly. Strings can be empty, and a three-letter alphabet makes matches common. Run it with `python3 check.py edit-distance --answer your_file.py`.

## Hunt the bugs first

`wrong.py` holds two wrong answers. Run `python3 check.py edit-distance`, read the smallest failing input for each, and work out why before you open these.

<details>
<summary>The gut answer</summary>

Comparing letters by position cannot see a shift. One letter inserted at the front makes every later position differ, yet the true distance is 1.

</details>

<details>
<summary>The planted bug</summary>

`planted` is `fast.py` with one line changed. It has `cost = 0 if x == y else 2` where the correct line is `cost = 0 if x == y else 1`. Costing a replacement 2 is the same as a delete plus an insert, so replacements stop being a useful move. The result is a different distance, and it agrees with the real one whenever no replacement is needed.

</details>
