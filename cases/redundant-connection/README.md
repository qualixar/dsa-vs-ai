# Redundant Connection

[LeetCode 684](https://leetcode.com/problems/redundant-connection/) | Graphs

**The problem.** A tree on nodes 1 to n has one extra edge added, so it now has exactly one cycle. Report the edge to remove to get a tree back. If several would do, report the one that appears last in the list.

**Signature here.** `solve(edges) -> [a, b]`

**The shape to notice.** Add edges one at a time. An edge whose two ends are already connected is the one that closes the cycle. Union-find answers "already connected?" in nearly constant time.

**The idea.** Give each node a parent pointer. For each edge, find the two roots. If they match, this edge closes the cycle and it is the last one that does. Otherwise link the two roots.

**Complexity.** Close to O(n) time and O(n) space. The slow machine is O(n^2).

**How an AI answer to this would be checked.** Compare the edge against slow's, which removes each edge from the back and tests connectivity with a search. The generator shuffles the edges so the cycle closes at varied places. Run it with `python3 check.py redundant-connection --answer your_file.py`.

## Hunt the bugs first

`wrong.py` holds two wrong answers. Run `python3 check.py redundant-connection`, read the smallest failing input for each, and work out why before you open these.

<details>
<summary>The gut answer</summary>

Seeing both ends before does not mean they are connected. Two separate pieces that are about to be joined look the same to a plain set.

</details>

<details>
<summary>The planted bug</summary>

`planted` is `fast.py` with one line changed. It has `parent[a] = rb` where the correct line is `parent[ra] = rb`. `a` may not be a root. Pointing it at the other root detaches `a` from its old group while leaving that group's root unlinked, so a later find gives the wrong answer about connection.

</details>
