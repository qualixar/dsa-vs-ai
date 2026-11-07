class Solution:
    def elevatorRequests(self, n: int, start: int, requests: list[int]) -> int:
        L = sorted([x for x in requests if x < start], reverse=True)
        R = sorted([x for x in requests if x > start])
        a, b = len(L), len(R)
        m = a + b
        INF = float('inf')
        posL = [start] + L
        posR = [start] + R
        # prev rows
        prev0 = None
        prev1 = None
        for i in range(a + 1):
            cur0 = [INF] * (b + 1)
            cur1 = [INF] * (b + 1)
            pl = posL[i]
            for j in range(b + 1):
                if i == 0 and j == 0:
                    cur0[0] = 0
                    cur1[0] = 0
                    continue
                if i > 0:
                    rem = m - (i - 1) - j
                    best = INF
                    v = prev0[j]
                    if v < INF:
                        best = v + (posL[i - 1] - pl) * rem
                    v = prev1[j]
                    if v < INF:
                        c = v + (posR[j] - pl) * rem
                        if c < best:
                            best = c
                    cur0[j] = best
                if j > 0:
                    rem = m - i - (j - 1)
                    pr = posR[j]
                    best = INF
                    v = cur0[j - 1]
                    if v < INF:
                        best = v + (pr - posL[i]) * rem
                    v = cur1[j - 1]
                    if v < INF:
                        c = v + (pr - posR[j - 1]) * rem
                        if c < best:
                            best = c
                    cur1[j] = best
                if i == 0:
                    cur0[j] = INF if j > 0 else cur0[j]
                if j == 0 and i > 0:
                    cur1[0] = INF
            prev0, prev1 = cur0, cur1
        return min(prev0[b], prev1[b])
