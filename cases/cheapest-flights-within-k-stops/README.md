# Cheapest Flights Within K Stops

[LeetCode 787](https://leetcode.com/problems/cheapest-flights-within-k-stops/) | Graphs

**The problem.** Flights link cities at given prices. Find the cheapest way from one city to another using at most k stops in between, or -1 if none exists.

**Signature here.** `solve(n, flights, src, dst, k) -> int, where flights holds [from, to, price]`

**The shape to notice.** A shortest path with a budget on the number of edges. Round i of Bellman-Ford finds the best cost using at most i edges, so the budget is the number of rounds.

**The idea.** Run k + 1 rounds of relaxation. In each round, read costs from a copy made at the start of the round, so that one round adds at most one flight.

**Complexity.** O(k * (n + F)) time and O(n) space for F flights, since each round copies the costs. The slow machine grows exponentially with k.

**How an AI answer to this would be checked.** Compare the price against slow's, which walks every allowed route. The stop limit ranges from 0 to 3 so that the cheapest route is often over budget. Run it with `python3 check.py cheapest-flights-within-k-stops --answer your_file.py`.

## Hunt the bugs first

`wrong.py` holds two wrong answers. Run `python3 check.py cheapest-flights-within-k-stops`, read the smallest failing input for each, and work out why before you open these.

<details>
<summary>The gut answer</summary>

A visited set records the cheapest arrival at a city, but that arrival may have used up the stops. A pricier arrival with stops to spare could still reach the destination, and it is thrown away.

</details>

<details>
<summary>The planted bug</summary>

`planted` is `fast.py` with one line changed. It has `before = cost` where the correct line is `before = cost[:]`. Without the copy, updates made earlier in a round feed later relaxations in the same round. A single round can then chain several flights, and the stop limit stops meaning anything. The code still gives right answers whenever the limit does not bind.

</details>
