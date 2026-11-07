class Solution:
    def elevatorRequests(self, n: int, start: int, requests: list[int]) -> int:
        p = sorted(set(requests + [start]))
        M = len(p)
        k = p.index(start)
        INF = float('inf')
        L = [INF] * M
        R = [INF] * M
        L[k] = R[k] = 0
        for ln in range(1, M):
            rem = M - ln
            nL = [INF] * M
            nR = [INF] * M
            lo = max(0, k - ln)
            hi = min(k, M - ln - 1)
            for i in range(lo, hi + 1):
                j = i + ln
                pi = p[i]
                pj = p[j]
                if i < k:
                    a = L[i + 1] + rem * (p[i + 1] - pi)
                    b = R[i + 1] + rem * (pj - pi)
                    nL[i] = a if a < b else b
                if j > k:
                    a = L[i] + rem * (pj - pi)
                    b = R[i] + rem * (pj - p[j - 1])
                    nR[i] = a if a < b else b
            L, R = nL, nR
        return min(L[0], R[0])
