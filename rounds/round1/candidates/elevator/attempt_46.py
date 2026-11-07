import numpy as np

class Solution:
    def elevatorRequests(self, n: int, start: int, requests: list[int]) -> int:
        left = sorted(start - r for r in requests if r < start)
        right = sorted(r - start for r in requests if r > start)
        p, q = len(left), len(right)
        T = p + q
        if T == 0:
            return 0
        INF = 10**18
        a = [0] + left
        b = np.array([0] + right, dtype=np.int64)
        js = np.arange(q + 1, dtype=np.int64)
        bdiff = np.zeros(q + 1, dtype=np.int64)
        if q > 0:
            bdiff[1:] = b[1:] - b[:-1]

        def compute_dp1(i, dp0):
            d = np.empty(q + 1, dtype=np.int64)
            d[0] = 0 if i == 0 else INF
            C = np.zeros(q + 1, dtype=np.int64)
            if q > 0:
                rem = T - i - js[1:] + 1
                d[1:] = dp0[:-1] + rem * (a[i] + b[1:])
                C[1:] = np.cumsum(rem * bdiff[1:])
            return C + np.minimum.accumulate(d - C)

        dp0 = np.full(q + 1, INF, dtype=np.int64)
        dp0[0] = 0
        dp1 = compute_dp1(0, dp0)
        for i in range(1, p + 1):
            rem = T - (i - 1) - js
            n0 = np.minimum(dp0 + rem * (a[i] - a[i - 1]), dp1 + rem * (b + a[i]))
            n0 = np.minimum(n0, INF)
            dp0 = n0
            dp1 = np.minimum(compute_dp1(i, dp0), INF)
        return int(min(dp0[q], dp1[q]))
