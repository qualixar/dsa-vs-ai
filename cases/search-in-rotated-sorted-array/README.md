# Search in Rotated Sorted Array

[LeetCode 33](https://leetcode.com/problems/search-in-rotated-sorted-array/) | Binary search

**The problem.** A sorted list of distinct numbers was cut at some point and its two parts swapped. Find the position of a target, or report -1, in logarithmic time.

**Signature here.** `solve(nums, target) -> int`

**The shape to notice.** Pick any midpoint and at least one side of it is still in sorted order. You can decide fully about that side.

**The idea.** At each step, find out which half is sorted by comparing its ends. If the target lies within that half's range, search there. Otherwise search the other half.

**Complexity.** O(log n) time and O(1) space. The slow machine is O(n).

**How an AI answer to this would be checked.** Compare the position against slow's, including targets that are absent and cuts at every point. The large input only finishes in time if the answer is close to linear or better; to confirm a logarithmic answer, read its loop. Run it with `python3 check.py search-in-rotated-sorted-array --answer your_file.py`.

## Hunt the bugs first

`wrong.py` holds two wrong answers. Run `python3 check.py search-in-rotated-sorted-array`, read the smallest failing input for each, and work out why before you open these.

<details>
<summary>The gut answer</summary>

Plain binary search assumes the whole list is sorted. On a rotated list it can step away from the target and report it missing.

</details>

<details>
<summary>The planted bug</summary>

`planted` is `fast.py` with one line changed. It has `if nums[lo] < nums[mid]:` where the correct line is `if nums[lo] <= nums[mid]:`. The comparison has to allow equality. When two elements remain, `lo` and `mid` are the same position, and that one-element half counts as sorted. With `<` the code picks the wrong half.

</details>
