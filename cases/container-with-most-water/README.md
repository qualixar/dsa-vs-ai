# Container With Most Water

[LeetCode 11](https://leetcode.com/problems/container-with-most-water/) | Two pointers

**The problem.** Vertical lines stand at evenly spaced positions. Pick two so that the container they form with the floor holds the most water. The area is the distance between them times the shorter line.

**Signature here.** `solve(heights) -> int`

**The shape to notice.** Start at maximum width. Every move inward loses width, so a move can only pay off if the height limit rises.

**The idea.** Two pointers start at the ends. The shorter line caps the area for every narrower pair that keeps it, so that line can be dropped for good. Move it inward.

**Complexity.** O(n) time and O(1) space. The slow machine is O(n^2).

**How an AI answer to this would be checked.** Compare the area against slow's. This case shows why the area alone is the thing to compare: many pairs can give the same best area. Run it with `python3 check.py container-with-most-water --answer your_file.py`.

## Hunt the bugs first

`wrong.py` holds two wrong answers. Run `python3 check.py container-with-most-water`, read the smallest failing input for each, and work out why before you open these.

<details>
<summary>The gut answer</summary>

The two tallest lines may be next to each other. Width counts as much as height, and a pair of shorter lines far apart can hold more.

</details>

<details>
<summary>The planted bug</summary>

`planted` is `fast.py` with one line changed. It has `if heights[lo] > heights[hi]:` where the correct line is `if heights[lo] < heights[hi]:`. This moves the taller line instead of the shorter one, which gives up the only line that could have improved the area.

</details>
