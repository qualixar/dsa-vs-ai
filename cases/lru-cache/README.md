# LRU Cache

[LeetCode 146](https://leetcode.com/problems/lru-cache/) | Linked structures

**The problem.** Build a key-value cache with a fixed capacity. When it is full and a new key arrives, it drops the key that has gone longest without being read or written. Reads and writes must be constant time. The check drives it with a list of operations and collects what the reads return.

**Signature here.** `solve(capacity, ops) -> list of int. Each op is ("get", key) or ("put", key, value); a missing key reads as -1.`

**The shape to notice.** You need to find a key quickly and also move it to the front of a line quickly. A hash map plus a doubly linked list does both, and an ordered dictionary is that pair in one object.

**The idea.** Treat dictionary order as recency. Reading or writing a key moves it to the back. Going over capacity removes the front.

**Complexity.** O(1) average per operation and O(capacity) space. The slow machine is O(capacity) per operation.

**How an AI answer to this would be checked.** Compare the list of reads against slow's. If you wrap a class answer, drive it from a `solve` with this signature. The operations are short and the capacity small, so evictions happen in nearly every run. Run it with `python3 check.py lru-cache --answer your_file.py`.

## Hunt the bugs first

`wrong.py` holds two wrong answers. Run `python3 check.py lru-cache`, read the smallest failing input for each, and work out why before you open these.

<details>
<summary>The gut answer</summary>

Evicting by first arrival is a FIFO cache. Reads and rewrites should count as use, so a key in constant use still gets thrown out here.

</details>

<details>
<summary>The planted bug</summary>

`planted` is `fast.py` with one line changed. It has `pass` where the correct line is `cache.pop(key, None)`. Assigning to a key already in the dictionary keeps its old place in the order. Rewriting a key must count as use, and without the removal it does not, so the wrong key is evicted later.

</details>
