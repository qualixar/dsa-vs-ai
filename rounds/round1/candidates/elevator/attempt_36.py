class Solution:
    def elevatorRequests(self, n: int, start: int, requests: list[int]) -> int:
        pts = sorted(set(requests) | {start})
        m = len(pts)
        s = pts.index(start)
        if m == 1:
            return 0
        INF = float('inf')
        dp0 = [INF] * m
        dp1 = [INF] * m
        dp0[s] = 0
        dp1[s] = 0
        p = pts
        for l in range(1, m):
            rem = m - l
            n0 = [INF] * m
            n1 = [INF] * m
            lo = max(0, s - l + 1)
            hi = min(s, m - l)
            for i in range(lo, hi + 1):
                j = i + l - 1
                a = dp0[i]
                b = dp1[i]
                if i > 0:
                    pi1 = p[i - 1]
                    v = min(a + (p[i] - pi1) * rem, b + (p[j] - pi1) * rem)
                    if v < n0[i - 1]:
                        n0[i - 1] = v
                if j < m - 1:
                    pj1 = p[j + 1]
                    v = min(a + (pj1 - p[i]) * rem, b + (pj1 - p[j]) * rem)
                    if v < n1[i]:
                        n1[i] = v
            dp0, dp1 = n0, n1
        return min(dp0[0], dp1[0])
