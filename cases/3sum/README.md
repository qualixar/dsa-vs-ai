# 3Sum

[LeetCode 15](https://leetcode.com/problems/3sum/) | Two pointers

**The problem.** Find every distinct set of three entries in a list whose values add up to zero. The same values must not be reported twice, though a value may appear more than once within a triple if the list really holds it that many times.

**Signature here.** `solve(nums) -> list of [a, b, c]`

**The shape to notice.** Fix one number and the rest is the two-ended search on sorted data. Sorting also puts duplicates side by side, which makes them easy to skip.

**The idea.** Sort. For each first value, skip it if it repeats the previous one, then close in from both ends of what follows, skipping repeats after each hit.

**Complexity.** O(n^2) time and O(n) space for the sorted copy, plus the output. The slow machine is O(n^3).

**How an AI answer to this would be checked.** Order does not matter, so both answers are sorted before comparing, and duplicates in an answer count as wrong. Small value ranges force many repeats, which is where this question breaks. Run it with `python3 check.py 3sum --answer your_file.py`.

## Hunt the bugs first

`wrong.py` holds two wrong answers. Run `python3 check.py 3sum`, read the smallest failing input for each, and work out why before you open these.

<details>
<summary>The gut answer</summary>

A set of values cannot tell how many copies of a number exist. A pair can look itself up, so the code invents triples that use one entry twice.

</details>

<details>
<summary>The planted bug</summary>

`planted` is `fast.py` with one line changed. It has `if i + 1 < len(nums) and nums[i] == nums[i + 1]:` where the correct line is `if i > 0 and nums[i] == nums[i - 1]:`. Both versions skip repeats, but this one skips the first copy instead of the later ones. The first copy is the one that can still use its twin as a partner, so triples with a repeated smallest value disappear.

</details>
