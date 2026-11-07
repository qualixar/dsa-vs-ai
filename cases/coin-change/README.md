# Coin Change

[LeetCode 322](https://leetcode.com/problems/coin-change/) | DP: 1D

**The problem.** Find the fewest coins that add up to an amount, with unlimited coins of each given value, or -1 if it cannot be done.

**Signature here.** `solve(coins, amount) -> int`

**The shape to notice.** The best answer for an amount comes from the best answer for a smaller amount, plus one coin. Each smaller amount only needs solving once.

**The idea.** Fill a table from 0 up. For each amount, try each coin as the last one used and take the smallest result.

**Complexity.** O(amount * coins) time and O(amount) space. The slow machine multiplies the counts of every coin.

**How an AI answer to this would be checked.** Compare the count against slow's, which tries all count combinations. Random coin sets rarely have the property that makes taking the largest first work, so this generator breaks greedy answers quickly. Run it with `python3 check.py coin-change --answer your_file.py`.

## Hunt the bugs first

`wrong.py` holds two wrong answers. Run `python3 check.py coin-change`, read the smallest failing input for each, and work out why before you open these.

<details>
<summary>The gut answer</summary>

Largest first works for most real currencies, which is why it feels right. With coins 1, 3 and 4 and amount 6, it takes three coins where two 3s are enough, and it can also miss solutions entirely.

</details>

<details>
<summary>The planted bug</summary>

`planted` is `fast.py` with one line changed. It has `if coin < total:` where the correct line is `if coin <= total:`. A coin exactly equal to the amount is the best possible move, and this test rules it out, so the base step of the table is never used.

</details>
