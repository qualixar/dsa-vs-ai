import numpy as np

class Solution:
    def elevatorRequests(self, n: int, start: int, requests: list[int]) -> int:
        left = sorted(start - x for x in requests if x < start)
        right = sorted(x - start for x in requests if x > start)
        a, b = len(left), len(right)
        m = a + b
        if m == 0:
            return 0
        INF = np.int64(10**18)
        pl = [0] + left
        pr = np.array([0] + right, dtype=np.int64)
        js = np.arange(b + 1, dtype=np.int64)
        prdiff = np.zeros(b + 1, dtype=np.int64)
        if b > 0:
            prdiff[1:] = pr[1:] - pr[:-1]

        prevL = None
        prevR = None
        for i in range(a + 1):
            # compute dpL row
            if i == 0:
                curL = np.full(b + 1, INF, dtype=np.int64)
                curL[0] = 0
            else:
                rem = m - (i - 1) - js
                o1 = prevL + rem * (pl[i] - pl[i - 1])
                o2 = prevR + rem * (pl[i] + pr)
                curL = np.minimum(np.minimum(o1, o2), INF)
            # compute dpR row
            x0 = 0 if i == 0 else INF
            curR = np.full(b + 1, INF, dtype=np.int64)
            curR[0] = x0
            if b > 0:
                remj = m - i - (js[1:] - 1)
                aj = remj * prdiff[1:]
                bj = curL[:-1] + remj * (pl[i] + pr[1:])
                bj = np.minimum(bj, INF)
                S = np.cumsum(aj)
                t = bj - S
                cm = np.minimum.accumulate(t)
                cm = np.minimum(cm, np.int64(x0))
                curR[1:] = np.minimum(S + cm, INF)
            prevL, prevR = curL, curR
        return int(min(prevL[b], prevR[b]))
