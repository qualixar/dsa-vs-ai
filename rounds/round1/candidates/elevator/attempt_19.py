class Solution:
    def elevatorRequests(self, n: int, start: int, requests: list[int]) -> int:
        reqset = set(requests)
        base = 0 if start in reqset else 1
        pts = sorted(reqset | {start})
        m = len(pts)
        R = len(requests)
        s = pts.index(start)
        if m == 1:
            return 0
        INF = float('inf')
        p = pts
        L = [INF] * m
        Rr = [INF] * m
        L[s] = 0
        Rr[s] = 0
        for ln in range(1, m):
            u = R - (ln - base)
            nl = ln + 1
            NL = [INF] * m
            NR = [INF] * m
            lo = max(0, s - nl + 1)
            hi = min(s, m - nl)
            for i in range(lo, hi + 1):
                j = i + nl - 1
                # newL: old interval [i+1, j]
                if i < s:
                    a = L[i + 1] + (p[i + 1] - p[i]) * u
                    b = Rr[i + 1] + (p[j] - p[i]) * u
                    NL[i] = a if a < b else b
                # newR: old interval [i, j-1]
                if j > s:
                    a = Rr[i] + (p[j] - p[j - 1]) * u
                    b = L[i] + (p[j] - p[i]) * u
                    NR[i] = a if a < b else b
            L, Rr = NL, NR
        return min(L[0], Rr[0])
