import numpy as np

class Solution:
    def elevatorRequests(self, n: int, start: int, requests: list[int]) -> int:
        reqset = set(requests)
        pts = sorted(reqset | {start})
        m = len(pts)
        if m == 1:
            return 0
        p = np.array(pts, dtype=np.int64)
        w = np.array([1 if x in reqset else 0 for x in pts], dtype=np.int64)
        pre = np.zeros(m + 1, dtype=np.int64)
        pre[1:] = np.cumsum(w)
        T = int(pre[m])
        s = pts.index(start)
        INF = 10**18
        L = np.full(m, INF, dtype=np.int64)
        R = np.full(m, INF, dtype=np.int64)
        L[s] = 0
        R[s] = 0
        for d in range(1, m):
            i = np.arange(m - d)
            j = i + d
            o1 = T - (pre[j + 1] - pre[i + 1])
            o2 = T - (pre[j] - pre[i])
            span = p[j] - p[i]
            Ln = np.minimum(L[1:] + (p[i + 1] - p[i]) * o1, R[1:] + span * o1)
            Rn = np.minimum(R[:-1] + (p[j] - p[j - 1]) * o2, L[:-1] + span * o2)
            np.minimum(Ln, INF, out=Ln)
            np.minimum(Rn, INF, out=Rn)
            L, R = Ln, Rn
        return int(min(L[0], R[0]))
