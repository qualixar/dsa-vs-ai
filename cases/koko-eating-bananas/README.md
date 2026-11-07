# Koko Eating Bananas

[LeetCode 875](https://leetcode.com/problems/koko-eating-bananas/) | Binary search

**The problem.** Piles of food must be finished within h hours. Each hour the eater works on one pile at a chosen fixed speed, and the rest of that hour is wasted if the pile runs out. Find the smallest speed that works.

**Signature here.** `solve(piles, h) -> int`

**The shape to notice.** You are searching over answers, not positions. If a speed works, every faster speed works too, so the yes and no answers fall into one clean split.

**The idea.** Binary search on the speed between 1 and the largest pile. For each candidate, add up the hours needed, rounding up per pile.

**Complexity.** O(n log m) time, where m is the largest pile, and O(1) space. The slow machine is O(n m).

**How an AI answer to this would be checked.** Compare the speed against slow's on small piles, which try hour limits from tight to loose. Run it with `python3 check.py koko-eating-bananas --answer your_file.py`.

## Hunt the bugs first

`wrong.py` holds two wrong answers. Run `python3 check.py koko-eating-bananas`, read the smallest failing input for each, and work out why before you open these.

<details>
<summary>The gut answer</summary>

Averaging ignores the wasted time at the end of each pile. Rounding happens per pile, not over the total, so the average speed is often too low.

</details>

<details>
<summary>The planted bug</summary>

`planted` is `fast.py` with one line changed. It has `hours = sum(p // speed + 1 for p in piles)` where the correct line is `hours = sum((p + speed - 1) // speed for p in piles)`. This adds an hour even when a pile is finished exactly on an hour boundary, so it overestimates the time and can settle on a speed that is too high.

</details>
