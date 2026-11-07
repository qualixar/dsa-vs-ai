# Meeting Rooms II

[LeetCode 253](https://leetcode.com/problems/meeting-rooms-ii/) | Intervals

**The problem.** Meetings have start and end times. Find the fewest rooms that fit all of them. A meeting that ends exactly when another begins can share the room. LeetCode's page for this one needs a subscription.

**Signature here.** `solve(meetings) -> int`

**The shape to notice.** What you care about is the room that frees up soonest. A min-heap of end times gives you exactly that one.

**The idea.** Process meetings by start time. If the earliest ending room is free by then, reuse it. Otherwise open a new room. The heap's size at the end is the answer.

**Complexity.** O(n log n) time and O(n) space. The slow machine is O(n^2).

**How an AI answer to this would be checked.** Compare the count against slow's, which measures overlap directly at each start time. Back-to-back meetings are common in the generated inputs, because that boundary is the usual failure. Run it with `python3 check.py meeting-rooms-ii --answer your_file.py`.

## Hunt the bugs first

`wrong.py` holds two wrong answers. Run `python3 check.py meeting-rooms-ii`, read the smallest failing input for each, and work out why before you open these.

<details>
<summary>The gut answer</summary>

A meeting that clashes with three others does not need four rooms if those three never overlap each other. Clashing with the same meeting is not the same as all running at once.

</details>

<details>
<summary>The planted bug</summary>

`planted` is `fast.py` with one line changed. It has `if rooms and rooms[0] < start:` where the correct line is `if rooms and rooms[0] <= start:`. The room is free at the moment the last meeting ends, so the test must allow equality. With `<`, back-to-back meetings each get their own room.

</details>
