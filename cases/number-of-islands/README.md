# Number of Islands

[LeetCode 200](https://leetcode.com/problems/number-of-islands/) | Graphs

**The problem.** A grid holds land (1) and water (0). Count the groups of land cells connected up, down, left or right.

**Signature here.** `solve(grid) -> int, where grid is a list of lists of 0 and 1`

**The shape to notice.** Each cell is a node and each pair of touching land cells is an edge. The question is how many connected components there are.

**The idea.** Scan the grid. Each unvisited land cell starts a new island. Flood from it with an explicit stack so that everything connected gets marked before the scan moves on.

**Complexity.** O(rows * cols) time and space. The slow machine repeats full passes until labels settle, so it can take many passes on a winding island.

**How an AI answer to this would be checked.** Compare the count against slow's, which labels cells instead of flooding them. Grids at these sizes produce U shapes often, and U shapes are what expose scan-order mistakes. Run it with `python3 check.py number-of-islands --answer your_file.py`.

## Hunt the bugs first

`wrong.py` holds two wrong answers. Run `python3 check.py number-of-islands`, read the smallest failing input for each, and work out why before you open these.

<details>
<summary>The gut answer</summary>

A U shape has two top-left corners but is one island. Counting corners only works when every island is a plain rectangle or similar.

</details>

<details>
<summary>The planted bug</summary>

`planted` is `fast.py` with one line changed. It has `if 0 < nx < rows and 0 <= ny < cols and grid[nx][ny] == 1 and (nx, ny) not in seen:` where the correct line is `if 0 <= nx < rows and 0 <= ny < cols and grid[nx][ny] == 1 and (nx, ny) not in seen:`. `0 < nx` shuts row 0 out of the flood. The scan still starts islands from cells in row 0, but the flood cannot move along that row or climb back up to it, so one island there gets counted as several.

</details>
