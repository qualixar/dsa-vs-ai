# Network Delay Time

[LeetCode 743](https://leetcode.com/problems/network-delay-time/) | Graphs

**The problem.** Nodes numbered from 1 to n are linked by one-way edges with travel times. A signal leaves node k. Find how long it takes to reach every node, or -1 if some node is never reached.

**Signature here.** `solve(times, n, k) -> int, where times holds [from, to, time]`

**The shape to notice.** Shortest paths from one source with non-negative weights. That is Dijkstra's algorithm, and the answer is the largest shortest distance.

**The idea.** Keep a heap of tentative arrivals. The earliest one is final, because every other route is already at least as long. Mark it and offer its neighbours.

**Complexity.** O(E log E) time and O(E) space. The slow machine is O(n * E).

**How an AI answer to this would be checked.** Compare the time against slow's, which relaxes every edge n times and needs no heap. Graphs with unreachable nodes are generated, so the -1 path is tested. Run it with `python3 check.py network-delay-time --answer your_file.py`.

## Hunt the bugs first

`wrong.py` holds two wrong answers. Run `python3 check.py network-delay-time`, read the smallest failing input for each, and work out why before you open these.

<details>
<summary>The gut answer</summary>

Fewest hops is not least time. A route with more edges can be faster, and breadth-first search treats every edge as equal.

</details>

<details>
<summary>The planted bug</summary>

`planted` is `fast.py` with one line changed. It has `heappush(heap, (w, v))` where the correct line is `heappush(heap, (d + w, v))`. This pushes the edge's own weight instead of the total distance. That is Prim's algorithm for a spanning tree, not shortest paths, and the code looks nearly the same as the right one.

</details>
