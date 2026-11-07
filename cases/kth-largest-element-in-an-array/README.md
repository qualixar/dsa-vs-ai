# Kth Largest Element in an Array

[LeetCode 215](https://leetcode.com/problems/kth-largest-element-in-an-array/) | Heaps

**The problem.** Find the value that would sit at rank k if a list were sorted from largest to smallest. Repeated values each take their own rank.

**Signature here.** `solve(nums, k) -> int`

**The shape to notice.** You only need the top k, not a full order. A small heap of the best k so far costs less than sorting.

**The idea.** Keep a min-heap of at most k values. When it grows past k, drop the smallest. What is left on top is the kth largest.

**Complexity.** O(n log k) time and O(k) space. The slow machine is O(n log n), and for this problem slow is not very slow; the reason to use it is that nobody doubts it.

**How an AI answer to this would be checked.** Compare the value against slow's. Small value ranges force repeats, which separates "kth largest" from "kth largest distinct". Run it with `python3 check.py kth-largest-element-in-an-array --answer your_file.py`.

## Hunt the bugs first

`wrong.py` holds two wrong answers. Run `python3 check.py kth-largest-element-in-an-array`, read the smallest failing input for each, and work out why before you open these.

<details>
<summary>The gut answer</summary>

Removing duplicates answers a different question. With repeats in the list, rank k lands on the wrong value.

</details>

<details>
<summary>The planted bug</summary>

`planted` is `fast.py` with one line changed. It has `if len(heap) > k + 1:` where the correct line is `if len(heap) > k:`. The heap keeps one value too many, so its smallest entry is the (k+1)th largest. It looks fine whenever the list has k items or fewer.

</details>
