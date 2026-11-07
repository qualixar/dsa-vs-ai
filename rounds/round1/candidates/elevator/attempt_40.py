import numpy as np

class Solution:
    def elevatorRequests(self, n: int, start: int, requests: list[int]) -> int:
        L = sorted([x for x in requests if x < start], reverse=True)
        R = sorted([x for x in requests if x > start])
        a, b = len(L), len(R)
        m = a + b
        if m == 0:
            return 0
        INF = np.int64(10**18)
        posL = [start] + L
        posR = np.array([start] + R, dtype=np.int64)
        js = np.arange(b + 1, dtype=np.int64)
        dR = np.zeros(b + 1, dtype=np.int64)
        dR[1:] = posR[1:] - posR[:-1]
        P0 = P1 = None
        for i in range(a + 1):
            if i == 0:
                new0 = np.full(b + 1, INF, dtype=np.int64)
                new0[0] = 0
            else:
                rem = m - (i - 1) - js
                new0 = np.minimum(P0 + (posL[i - 1] - posL[i]) * rem,
                                  P1 + (posR - posL[i]) * rem)
                new0 = np.minimum(new0, INF)
            # new1
            f0 = np.int64(0) if i == 0 else INF
            if b > 0:
                remp = m - i - js[1:] + 1
                g = new0[:-1] + (posR[1:] - posL[i]) * remp
                c = dR[1:] * remp
                C = np.cumsum(c)
                vals = g - C
                h = np.minimum.accumulate(np.concatenate(([f0], vals)))
                new1 = np.empty(b + 1, dtype=np.int64)
                new1[0] = f0
                new1[1:] = h[1:] + C
                new1 = np.minimum(new1, INF)
            else:
                new1 = np.array([f0], dtype=np.int64)
            P0, P1 = new0, new1
        return int(min(P0[b], P1[b]))
