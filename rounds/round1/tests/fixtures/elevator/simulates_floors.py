class Solution:
    def elevatorRequests(self, n: int, start: int, requests: list[int]) -> int:
        floors = [0] * n  # one slot per floor: fine for small n, not for 10^9
        from itertools import permutations
        rest = [r for r in requests if r != start]
        best = None
        for order in permutations(rest):
            pos, t, total, done = start, 0, 0, set()
            for tg in order:
                if tg in done: continue
                lo, hi = sorted((pos, tg))
                for r in order:
                    if r not in done and lo <= r <= hi:
                        done.add(r); total += t + abs(r - pos)
                t += abs(tg - pos); pos = tg
            best = total if best is None else min(best, total)
        return best or 0
