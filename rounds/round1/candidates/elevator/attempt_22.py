import numpy as np

class Solution:
    def elevatorRequests(self, n: int, start: int, requests: list[int]) -> int:
        a = sorted(start - x for x in requests if x < start)
        b = sorted(x - start for x in requests if x > start)
        p, q = len(a), len(b)
        K = p + q
        if K == 0:
            return 0
        INF = np.int64(10**18)
        J = np.arange(q + 1, dtype=np.int64)
        posR = np.array([0] + b, dtype=np.int64)
        bb = np.array(b, dtype=np.int64)
        prevposR = posR[:-1]  # posR(j-1) for j=1..q

        def posL(i):
            return -a[i - 1] if i > 0 else 0

        def compute_R(i, Lrow, x0):
            # dpR[i][j] for j=0..q
            if q == 0:
                return np.array([x0], dtype=np.int64)
            Jr = J[1:]
            remp = K - i - (Jr - 1)
            pl = posL(i)
            y = np.empty(q + 1, dtype=np.int64)
            y[0] = x0
            y[1:] = Lrow[:-1] + (bb - pl) * remp
            # cap INF-derived values
            y[1:] = np.where(Lrow[:-1] >= INF, INF, y[1:])
            c = (bb - prevposR) * remp
            C = np.zeros(q + 1, dtype=np.int64)
            C[1:] = np.cumsum(c)
            x = C + np.minimum.accumulate(y - C)
            return x

        L = np.full(q + 1, INF, dtype=np.int64)
        L[0] = 0
        R = compute_R(0, L, np.int64(0))
        for i in range(1, p + 1):
            ai = a[i - 1]
            rem = K - (i - 1) - J
            pl_prev = posL(i - 1)
            opt1 = np.where(L >= INF, INF, L + (pl_prev + ai) * rem)
            opt2 = np.where(R >= INF, INF, R + (posR + ai) * rem)
            newL = np.minimum(opt1, opt2)
            newR = compute_R(i, newL, INF)
            L, R = newL, newR
        return int(min(L[q], R[q]))
