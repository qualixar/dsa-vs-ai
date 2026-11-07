# Word Ladder

[LeetCode 127](https://leetcode.com/problems/word-ladder/) | Graphs

**The problem.** Change a start word into an end word one letter at a time, where each word along the way must be in a given list. Find how many words the shortest chain holds, counting both ends, or 0 if no chain exists.

**Signature here.** `solve(begin, end, words) -> int`

**The shape to notice.** Words are nodes and a one-letter change is an edge. All edges cost the same, so the shortest chain is a breadth-first search.

**The idea.** Search level by level from the start word. To find neighbours quickly, index every word under its patterns such as `c*t`, so words that differ by one letter share a key.

**Complexity.** O(n * L^2) time and O(n * L^2) space for n words of length L. The slow machine walks every simple path, which grows faster than exponentially in the number of words.

**How an AI answer to this would be checked.** Compare the length against slow's, which enumerates every simple path. Inputs include end words that are missing and start words that are not in the list. Run it with `python3 check.py word-ladder --answer your_file.py`.

## Hunt the bugs first

`wrong.py` holds two wrong answers. Run `python3 check.py word-ladder`, read the smallest failing input for each, and work out why before you open these.

<details>
<summary>The gut answer</summary>

Getting closer to the end word by letters does not mean getting closer along the chain. The best next step can look like a move away, and walking greedily with no way back can also dead-end.

</details>

<details>
<summary>The planted bug</summary>

`planted` is `fast.py` with one line changed. It has `word, length = queue.pop()` where the correct line is `word, length = queue.popleft()`. One word changes breadth-first into depth-first. The search still finds a chain, but not always the shortest, and it stops at the first one it reaches.

</details>
