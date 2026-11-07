# Course Schedule II

[LeetCode 210](https://leetcode.com/problems/course-schedule-ii/) | Graphs

**The problem.** Courses numbered from 0 have prerequisite pairs. Give any order that takes each course after its prerequisites, or an empty list if a loop makes that impossible.

**Signature here.** `solve(n, prereqs) -> list of int, where prereqs holds [course, needed_first]`

**The shape to notice.** A dependency graph. An order that respects every edge is a topological sort, and one exists exactly when the graph has no cycle.

**The idea.** Count each course's unmet prerequisites. Courses at zero are ready. Taking one lowers the counts of those that depend on it. If some courses never reach zero, there is a cycle.

**Complexity.** O(n + p) time and space for p pairs. The slow machine tries up to n! orders.

**How an AI answer to this would be checked.** Many orders can be right, so the check tests the order itself: every course appears once and each pair is respected. Slow only decides whether any order exists. Run it with `python3 check.py course-schedule-ii --answer your_file.py`.

## Hunt the bugs first

`wrong.py` holds two wrong answers. Run `python3 check.py course-schedule-ii`, read the smallest failing input for each, and work out why before you open these.

<details>
<summary>The gut answer</summary>

The number of prerequisites says nothing about which courses they are. A course with one prerequisite can come before that prerequisite in this order, and loops go undetected.

</details>

<details>
<summary>The planted bug</summary>

`planted` is `fast.py` with one line changed. It has `return order` where the correct line is `return order if len(order) == n else []`. Courses caught in a loop never become ready, so a partial list comes out. Returning it reports success where the correct answer is that no order exists.

</details>
