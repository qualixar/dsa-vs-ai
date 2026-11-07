class Solution:
    def elevatorRequests(self, n: int, start: int, requests: list[int]) -> int:
        A = sorted(start - r for r in requests if r < start)
        B = sorted(r - start for r in requests if r > start)
        a, b = len(A), len(B)
        k = a + b
        if k == 0:
            return 0
        INF = float('inf')
        dpL = [[INF] * (b + 1) for _ in range(a + 1)]
        dpR = [[INF] * (b + 1) for _ in range(a + 1)]
        for i in range(a + 1):
            Li = dpL[i]
            Ri = dpR[i]
            if i >= 1:
                Lp = dpL[i - 1]
                Rp = dpR[i - 1]
                ai = A[i - 1]
                da = ai - A[i - 2] if i >= 2 else 0
            for j in range(b + 1):
                if i >= 1:
                    if i == 1 and j == 0:
                        Li[j] = k * A[0]
                    else:
                        rem = k - (i - 1) - j
                        best = INF
                        if i >= 2:
                            v = Lp[j] + rem * da
                            if v < best:
                                best = v
                        if j >= 1:
                            v = Rp[j] + rem * (B[j - 1] + ai)
                            if v < best:
                                best = v
                        Li[j] = best
                if j >= 1:
                    if i == 0 and j == 1:
                        Ri[j] = k * B[0]
                    else:
                        rem = k - i - (j - 1)
                        best = INF
                        bj = B[j - 1]
                        if j >= 2:
                            v = Ri[j - 1] + rem * (bj - B[j - 2])
                            if v < best:
                                best = v
                        if i >= 1:
                            v = Li[j - 1] + rem * (A[i - 1] + bj)
                            if v < best:
                                best = v
                        Ri[j] = best
        return min(dpL[a][b], dpR[a][b])
