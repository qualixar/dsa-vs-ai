import numpy as np

class Solution:
    def elevatorRequests(self, n: int, start: int, requests: list[int]) -> int:
        left = sorted([x for x in requests if x < start], reverse=True)
        right = sorted([x for x in requests if x > start])
        a, b = len(left), len(right)
        total = a + b
        if total == 0:
            return 0
        PL = np.array([start] + left, dtype=np.int64)
        PR = np.array([start] + right, dtype=np.int64)
        INF = np.int64(4 * 10**18)
        A = np.full((a + 1, b + 1), INF, dtype=np.int64)
        B = np.full((a + 1, b + 1), INF, dtype=np.int64)
        A[0, 0] = 0
        B[0, 0] = 0
        for k in range(1, total + 1):
            lo = max(0, k - b)
            hi = min(a, k)
            I = np.arange(lo, hi + 1, dtype=np.int64)
            J = k - I
            rem = total - (k - 1)
            # A: arrive at left, I >= 1
            m = I >= 1
            if m.any():
                Ii = I[m]
                Jj = J[m]
                c1 = A[Ii - 1, Jj] + (PL[Ii - 1] - PL[Ii]) * rem
                c2 = B[Ii - 1, Jj] + (PR[Jj] - PL[Ii]) * rem
                A[Ii, Jj] = np.minimum(np.minimum(c1, c2), INF)
            m = J >= 1
            if m.any():
                Ii = I[m]
                Jj = J[m]
                c1 = B[Ii, Jj - 1] + (PR[Jj] - PR[Jj - 1]) * rem
                c2 = A[Ii, Jj - 1] + (PR[Jj] - PL[Ii]) * rem
                B[Ii, Jj] = np.minimum(np.minimum(c1, c2), INF)
        return int(min(A[a, b], B[a, b]))
