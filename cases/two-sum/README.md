# Two Sum

[LeetCode 1](https://leetcode.com/problems/two-sum/) | Arrays and hashing

**The problem.** You get a list of whole numbers and a target. Find the positions of two different entries that add up to the target. This version also allows the case where no pair exists, and then the answer is `None`.

**Signature here.** `solve(nums, target) -> [i, j] or None`

**The shape to notice.** For each number you know exactly what partner it needs. A question of the form "have I already seen this value?" is a job for a hash map.

**The idea.** Walk the list once. Before storing a number, look up the partner it needs among the numbers already passed. Checking before storing is what stops a number pairing with itself.

**Complexity.** O(n) time and O(n) space. The slow machine is O(n^2) time and O(1) space.

**How an AI answer to this would be checked.** Many pairs can be valid, so the check does not compare against slow's pair. It confirms the two positions differ and that their values add up, and it uses slow only to learn whether any pair exists. Run it with `python3 check.py two-sum --answer your_file.py`.

## Hunt the bugs first

`wrong.py` holds two wrong answers. Run `python3 check.py two-sum`, read the smallest failing input for each, and work out why before you open these.

<details>
<summary>The gut answer</summary>

Sorting and closing in from both ends does find whether a pair exists, and it is a real technique. But sorting throws away the original positions, and the question asks for positions. It reports where the numbers landed after the sort.

</details>

<details>
<summary>The planted bug</summary>

`planted` is `fast.py` with one line changed. It has `seen = {nums[0]: 0}` where the correct line is `seen = {}`. Starting the map with the first number already in it means the first number can pair with itself. It only goes wrong when the target is exactly twice the first number, so most inputs pass.

</details>
