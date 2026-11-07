# The case library

43 classic algorithm problems, written for practice. **This library is not a measurement of any AI.** No AI was run on these cases and nothing here says how one would do. The measured results are in [`../rounds/`](../rounds/README.md).

Each case folder holds:

| File | What it is |
|---|---|
| `README.md` | The problem in our own words, a link to LeetCode, the shape to notice, the idea, complexity, how an answer gets checked, and the two bugs behind a fold |
| `slow.py` | A brute force that is easy to believe. This is the answer key |
| `fast.py` | An efficient solution |
| `wrong.py` | `gut`, a tempting wrong idea, and `planted`, a copy of `fast.py` with exactly one line changed |
| `cases.py` | A generator of small inputs, one large input with a check of its answer, inputs at the 32-bit limits where width matters, and a custom comparison where several answers can be right |

`structures.py` holds the linked list and tree classes that some cases share, and `checking.py` holds the strict comparisons.

## Run it

```bash
python3 check.py --list
python3 check.py two-sum
python3 check.py --all
```

For each case the runner draws 3,000 small random inputs, removes duplicates and asks `slow.py` for each answer. Then it requires three things:

1. `fast.py` agrees with `slow.py` on every input, and finishes the large input within 10 seconds with an answer that a separate check accepts. That check works by another method, by construction or from the definition, since `slow.py` is too slow at that size.
2. `gut` fails on at least one input.
3. `planted` fails on at least one input.

A wrong answer that survives fails the whole case, so a claim in `wrong.py` cannot stand without a run. A crash or a call that takes over 2 seconds counts as a failure, and so does an answer of the wrong type or shape: `True` is not `1`, `1.0` is not `1`, a tuple is not a list, and an index must be in range.

Inputs can reach the ends of the 32-bit range even where LeetCode's stated limits are narrower, because a mask that is too narrow or a stand-in for infinity passes on small numbers.

## How to read a case

Read the README down to "Hunt the bugs first" and try the problem yourself. Then run the check, take the smallest failing input for `gut` and for `planted`, and work out what went wrong. Only then open the folds. `planted` is a good exercise on its own: open `wrong.py` and find the changed line.

## What these results do not show

- "Agrees" means no disagreement on the inputs tried. It is not a proof that `fast.py` is correct.
- "Smallest input" means the smallest among inputs tried, measured by the length of its text. A smaller one may exist.
- Complexity statements are reasoned, not measured. The runner applies a time limit to one large input and does not measure growth, so a solution that is correct and slower than stated could still pass.
- The large-input check tests one input. Most wrong answers are caught on small inputs, and some would pass the large one: for a large input where the answer is simply yes, always saying yes passes.
- `slow.py` is also code. It is kept short and usually takes a different route from `fast.py`, which makes a shared mistake less likely but not impossible.
- Inputs come from a generator, so a mistake the generator cannot produce goes unseen. In `cheapest-flights-within-k-stops`, plain random graphs let `gut` survive 2,998 inputs. The runner flagged that, and the generator now builds the input that exposes it.
- Random draws can differ across Python versions, so counts in the table may change on another version. The verdicts should not.

## About the LeetCode links

Numbers, titles and addresses belong to LeetCode. All 43 were checked against LeetCode's public GraphQL endpoint on 7 November 2026. The problem statements here are our own wording, and no LeetCode statement, example or editorial is copied. Go to LeetCode for the official text. The page for Meeting Rooms II needs a subscription.

## Add a case

Make a folder with the same five files. `cases.py` needs `TITLE`, `FAMILY`, `LEETCODE` (a number and address, or `None`), `MAX_SIZE`, `generate(rng, size)`, `big(rng)` and `big_check(args, got)`. Both generators return a tuple of arguments, and `big` must give the same input for the same seed. Add `same(args, got, want)` when several answers can be right, and `edges()` for inputs that must always be tried. Then run `python3 check.py your-case`, and `python3 -m unittest discover -s tests` for the rules each case must follow.

## Results

<!-- results table begins: written by check.py --write-table, do not edit -->
Written by `check.py --all --write-table` with Python 3.15, 3000 draws per case, seed 1. Inputs counts distinct inputs after duplicates are removed.

| Case | Family | Inputs | Fast vs slow | Gut fails | Gut's smallest failing input | Planted fails | Planted's smallest failing input |
|---|---|---:|---|---:|---|---:|---|
| [product-of-array-except-self](product-of-array-except-self/) | Arrays and hashing | 2117 | agree | 770 | `nums=[0]` | 2090 | `nums=[2, 3]` |
| [subarray-sum-equals-k](subarray-sum-equals-k/) | Arrays and hashing | 2392 | agree | 1268 | `nums=[1], k=0` | 842 | `nums=[1], k=1` |
| [two-sum](two-sum/) | Arrays and hashing | 2977 | agree | 1253 | `nums=[1, 0, 1], target=1` | 132 | `nums=[0, 1], target=0` |
| [3sum](3sum/) | Two pointers | 2014 | agree | 1035 | `nums=[0, 0]` | 230 | `nums=[0, 0, 0]` |
| [container-with-most-water](container-with-most-water/) | Two pointers | 2752 | agree | 1694 | `heights=[4, 5, 5]` | 1743 | `heights=[9, 9, 1]` |
| [trapping-rain-water](trapping-rain-water/) | Two pointers | 1965 | agree | 265 | `heights=[5, 3, 3, 0, 4]` | 1093 | `heights=[4, 0, 4]` |
| [longest-substring-without-repeating-characters](longest-substring-without-repeating-characters/) | Sliding window | 1698 | agree | 246 | `s='cbca'` | 677 | `s='dbbd'` |
| [minimum-window-substring](minimum-window-substring/) | Sliding window | 2540 | agree | 147 | `s='abca', t='ac'` | 992 | `s='ab', t='b'` |
| [sliding-window-maximum](sliding-window-maximum/) | Sliding window | 2585 | agree | 398 | `nums=[5, 2, 0], k=2` | 1117 | `nums=[4, 0], k=1` |
| [koko-eating-bananas](koko-eating-bananas/) | Binary search | 2563 | agree | 1637 | `piles=[9, 7], h=8` | 1448 | `piles=[3], h=3` |
| [median-of-two-sorted-arrays](median-of-two-sorted-arrays/) | Binary search | 2682 | agree | 1394 | `a=[0, 0], b=[5]` | 1064 | `a=[], b=[3]` |
| [search-in-rotated-sorted-array](search-in-rotated-sorted-array/) | Binary search | 2875 | agree | 287 | `nums=[3, 1], target=1` | 34 | `nums=[3, 1], target=1` |
| [evaluate-reverse-polish-notation](evaluate-reverse-polish-notation/) | Stacks | 2532 | agree | 534 | `items=['7', '-6', '/']` | 1168 | `items=['1', '9', '-']` |
| [largest-rectangle-in-histogram](largest-rectangle-in-histogram/) | Stacks | 2348 | agree | 1566 | `heights=[2, 6, 5]` | 837 | `heights=[2]` |
| [valid-parentheses](valid-parentheses/) | Stacks | 1546 | agree | 26 | `s=')('` | 70 | `s='['` |
| [kth-largest-element-in-an-array](kth-largest-element-in-an-array/) | Heaps | 2534 | agree | 896 | `nums=[3, 3, 1], k=2` | 1458 | `nums=[3, 1], k=1` |
| [merge-k-sorted-lists](merge-k-sorted-lists/) | Heaps | 1439 | agree | 710 | `lists=[[1, 7], [2]]` | 694 | `lists=[[1, 7], [2]]` |
| [meeting-rooms-ii](meeting-rooms-ii/) | Intervals | 2314 | agree | 909 | `meetings=[[3, 8], [7, 9], [2, 6]]` | 702 | `meetings=[[1, 2], [0, 1]]` |
| [merge-intervals](merge-intervals/) | Intervals | 2634 | agree | 1321 | `intervals=[[4, 9], [0, 2], [3, 8]]` | 820 | `intervals=[[5, 6], [4, 8]]` |
| [linked-list-cycle](linked-list-cycle/) | Linked structures | 1799 | agree | 791 | `head=[1, 1]` | 837 | `head=[2, 0]` |
| [lru-cache](lru-cache/) | Linked structures | 2681 | agree | 82 | `capacity=2, ops=[('put', 3, 8), ('put', 3, 4), ('get', 2)...` | 44 | `capacity=2, ops=[('put', 3, 8), ('put', 3, 4), ('get', 2)...` |
| [reverse-nodes-in-k-group](reverse-nodes-in-k-group/) | Linked structures | 2337 | agree | 442 | `head=[3, 4], k=3` | 1902 | `head=[4, 5], k=1` |
| [binary-tree-maximum-path-sum](binary-tree-maximum-path-sum/) | Trees | 2485 | agree | 408 | `root=[2, 4, 5]` | 388 | `root=[1, -2]` |
| [validate-binary-search-tree](validate-binary-search-tree/) | Trees | 2094 | agree | 120 | `root=[1, None, 3, 0]` | 117 | `root=[6, 6]` |
| [cheapest-flights-within-k-stops](cheapest-flights-within-k-stops/) | Graphs | 3000 | agree | 914 | `n=6, flights=[[0, 2, 2], [2, 1, 1], [0, 1, 6], [5, 4, 1],...` | 944 | `n=3, flights=[[1, 2, 4], [2, 0, 1]], src=1, dst=0, k=0` |
| [course-schedule-ii](course-schedule-ii/) | Graphs | 1342 | agree | 729 | `n=2, prereqs=[[1, 0], [0, 1]]` | 368 | `n=5, prereqs=[[4, 1], [1, 4]]` |
| [network-delay-time](network-delay-time/) | Graphs | 2428 | agree | 40 | `times=[[1, 3, 2], [1, 2, 8], [3, 2, 5]], n=3, k=1` | 621 | `times=[[2, 3, 6], [3, 1, 4]], n=3, k=2` |
| [number-of-islands](number-of-islands/) | Graphs | 1014 | agree | 331 | `grid=[[0, 1], [1, 1]]` | 442 | `grid=[[1, 1]]` |
| [redundant-connection](redundant-connection/) | Graphs | 2472 | agree | 1565 | `edges=[[1, 3], [2, 4], [1, 4], [3, 4]]` | 1729 | `edges=[[1, 3], [1, 2], [2, 3]]` |
| [word-ladder](word-ladder/) | Graphs | 2929 | agree | 32 | `begin='cac', end='bbb', words=['bac', 'abb', 'cab', 'cbb'...` | 27 | `begin='ccb', end='aca', words=['acb', 'acc', 'ccc', 'aca']` |
| [jump-game](jump-game/) | Greedy | 2114 | agree | 211 | `nums=[2, 2, 0, 0]` | 613 | `nums=[2, 0, 1]` |
| [non-overlapping-intervals](non-overlapping-intervals/) | Greedy | 2368 | agree | 201 | `intervals=[[3, 4], [1, 6], [5, 8]]` | 897 | `intervals=[[4, 6], [2, 4]]` |
| [combination-sum](combination-sum/) | Backtracking | 2447 | agree | 1260 | `candidates=[4, 2], target=8` | 1552 | `candidates=[1], target=8` |
| [word-search](word-search/) | Backtracking | 2205 | agree | 175 | `board=[['b', 'a', 'b']], word='bb'` | 68 | `board=[['a', 'b', 'b']], word='bba'` |
| [coin-change](coin-change/) | DP: 1D | 2658 | agree | 588 | `coins=[4, 5], amount=8` | 1850 | `coins=[4], amount=8` |
| [longest-increasing-subsequence](longest-increasing-subsequence/) | DP: 1D | 2189 | agree | 1082 | `nums=[5, 4, 5]` | 1186 | `nums=[2, 2]` |
| [edit-distance](edit-distance/) | DP: 2D | 916 | agree | 270 | `a='ab', b='b'` | 413 | `a='b', b='c'` |
| [partition-equal-subset-sum](partition-equal-subset-sum/) | DP: 2D | 2431 | agree | 201 | `nums=[7, 9, 5, 8, 5]` | 189 | `nums=[1, 5]` |
| [burst-balloons](burst-balloons/) | DP: intervals | 1968 | agree | 1420 | `nums=[2, 4, 4]` | 1903 | `nums=[4, 3]` |
| [partition-to-k-equal-sum-subsets](partition-to-k-equal-sum-subsets/) | DP: bitmask | 2534 | agree | 24 | `nums=[6, 4, 5, 6, 3, 4], k=2` | 260 | `nums=[1, 2], k=3` |
| [implement-trie-prefix-tree](implement-trie-prefix-tree/) | Tries | 2459 | agree | 209 | `ops=[('insert', 'bba'), ('prefix', 'a')]` | 379 | `ops=[('insert', 'ba'), ('search', 'b')]` |
| [counting-bits](counting-bits/) | Bit tricks | 201 | agree | 197 | `n=4` | 199 | `n=2` |
| [single-number-ii](single-number-ii/) | Bit tricks | 2791 | agree | 2481 | `nums=[7, 8, 8, 8]` | 1404 | `nums=[-5]` |
<!-- results table ends -->
