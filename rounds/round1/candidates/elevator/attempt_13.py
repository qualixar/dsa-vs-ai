import numpy as np

class Solution:
    def elevatorRequests(self, n: int, start: int, requests: list[int]) -> int:
        pts = sorted(set(requests) | {start})
        m = len(pts)
        if m == 1:
            return 0
        s = pts.index(start)
        p = np.array(pts, dtype=np.int64)
        INF = np.int64(10**18)
        L = np.full(m, INF, dtype=np.int64)
        R = np.full(m, INF, dtype=np.int64)
        L[s] = 0
        R[s] = 0
        for ln in range(1, m):
            rem = m - ln
            k = m - ln
            nL = np.full(m, INF, dtype=np.int64)
            nR = np.full(m, INF, dtype=np.int64)
            a = L[1:k + 1] + (p[1:k + 1] - p[0:k]) * rem
            b = R[1:k + 1] + (p[ln:m] - p[0:k]) * rem
            nL[0:k] = np.minimum(np.minimum(a, b), INF)
            c = L[0:k] + (p[ln:m] - p[0:k]) * rem
            d = R[0:k] + (p[ln:m] - p[ln - 1:m - 1]) * rem
            nR[0:k] = np.minimum(np.minimum(c, d), INF)
            L, R = nL, nR
        return int(min(L[0], R[0]))
