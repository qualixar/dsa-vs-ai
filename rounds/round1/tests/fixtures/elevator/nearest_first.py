class Solution:
    def elevatorRequests(self, n: int, start: int, requests: list[int]) -> int:
        rest = sorted(r for r in requests if r != start)
        pos, t, total = start, 0, 0
        while rest:
            nxt = min(rest, key=lambda r: (abs(r - pos), r))
            lo, hi = sorted((pos, nxt))
            for r in [x for x in rest if lo <= x <= hi]:
                total += t + abs(r - pos); rest.remove(r)
            t += abs(nxt - pos); pos = nxt
        return total
