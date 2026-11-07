class Solution:
    def elevatorRequests(self, n: int, start: int, requests: list[int]) -> int:
        a = sorted(start - x for x in requests if x < start)
        b = sorted(x - start for x in requests if x > start)
        p, q = len(a), len(b)
        m = p + q
        a = [0] + a
        b = [0] + b
        INF = float('inf')
        dp0 = [[INF] * (q + 1) for _ in range(p + 1)]
        dp1 = [[INF] * (q + 1) for _ in range(p + 1)]
        dp0[0][0] = 0
        dp1[0][0] = 0
        for i in range(p + 1):
            r0 = dp0[i]
            r1 = dp1[i]
            pr0 = dp0[i - 1] if i > 0 else None
            pr1 = dp1[i - 1] if i > 0 else None
            ai = a[i]
            for j in range(q + 1):
                if i == 0 and j == 0:
                    continue
                rem = m - i - j + 1
                if i > 0:
                    v = pr0[j] + (ai - a[i - 1]) * rem
                    w = pr1[j] + (ai + b[j]) * rem
                    r0[j] = v if v < w else w
                if j > 0:
                    v = r1[j - 1] + (b[j] - b[j - 1]) * rem
                    w = r0[j - 1] + (ai + b[j]) * rem
                    r1[j] = v if v < w else w
        return min(dp0[p][q], dp1[p][q])
