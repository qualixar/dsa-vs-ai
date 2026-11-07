class Solution:
    def elevatorRequests(self, n: int, start: int, requests: list[int]) -> int:
        l = sorted([x for x in requests if x < start], reverse=True)
        r = sorted([x for x in requests if x > start])
        a, b = len(l), len(r)
        m = a + b
        if m == 0:
            return 0
        INF = float('inf')
        Lp = [start] + l
        Rp = [start] + r
        curL = [INF] * (b + 1)
        curR = [INF] * (b + 1)
        curL[0] = 0
        curR[0] = 0
        for i in range(a + 1):
            nL = [INF] * (b + 1)
            nR = [INF] * (b + 1)
            lp = Lp[i]
            nxtl = l[i] if i < a else None
            for j in range(b + 1):
                cl = curL[j]
                cr = curR[j]
                if cl == INF and cr == INF:
                    continue
                rem = m - i - j
                rp = Rp[j]
                if i < a:
                    v = min(cl + (lp - nxtl) * rem, cr + (rp - nxtl) * rem)
                    if v < nL[j]:
                        nL[j] = v
                if j < b:
                    nr = r[j]
                    v = min(cl + (nr - lp) * rem, cr + (nr - rp) * rem)
                    if v < curR[j + 1]:
                        curR[j + 1] = v
            if i == a:
                return min(curL[b], curR[b])
            curL, curR = nL, nR
        return 0
