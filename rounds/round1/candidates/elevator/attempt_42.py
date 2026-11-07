import numpy as np

class Solution:
    def elevatorRequests(self, n: int, start: int, requests: list[int]) -> int:
        reqset = set(requests)
        pts = sorted(reqset | {start})
        m = len(pts)
        p = np.array(pts, dtype=np.int64)
        w = np.array([1 if x in reqset else 0 for x in pts], dtype=np.int64)
        W = np.zeros(m + 1, dtype=np.int64)
        W[1:] = np.cumsum(w)
        total = int(W[m])
        s = pts.index(start)
        INF = 10**18
        L = np.full(m, INF, dtype=np.int64)
        R = np.full(m, INF, dtype=np.int64)
        L[s] = 0
        R[s] = 0
        for ln in range(1, m):
            i = np.arange(m - ln)
            j = i + ln
            # interval [i+1, j] -> old index i+1
            rem1 = total - (W[j + 1] - W[i + 1])
            a = L[i + 1] + rem1 * (p[i + 1] - p[i])
            b = R[i + 1] + rem1 * (p[j] - p[i])
            newL = np.minimum(a, b)
            # interval [i, j-1] -> old index i
            rem2 = total - (W[j] - W[i])
            c = L[i] + rem2 * (p[j] - p[i])
            d = R[i] + rem2 * (p[j] - p[j - 1])
            newR = np.minimum(c, d)
            newL = np.minimum(newL, INF)
            newR = np.minimum(newR, INF)
            L, R = newL, newR
        return int(min(L[0], R[0]))
