class Solution:
    def elevatorRequests(self, n: int, start: int, requests: list[int]) -> int:
        L = sorted([x for x in requests if x < start], reverse=True)
        R = sorted([x for x in requests if x > start])
        a, b = len(L), len(R)
        m = a + b
        if m == 0:
            return 0
        INF = float('inf')
        P0 = [start] + L
        P1 = [start] + R
        dp0 = [[INF] * (b + 1) for _ in range(a + 1)]
        dp1 = [[INF] * (b + 1) for _ in range(a + 1)]
        dp0[0][0] = 0
        dp1[0][0] = 0
        for i in range(a + 1):
            d0 = dp0[i]
            d1 = dp1[i]
            if i > 0:
                p0 = dp0[i - 1]
                p1 = dp1[i - 1]
                li = L[i - 1]
                prevpos = P0[i - 1]
            for j in range(b + 1):
                if i == 0 and j == 0:
                    continue
                if i >= 1:
                    rem = m - (i - 1) - j
                    v1 = p0[j] + (prevpos - li) * rem
                    v2 = p1[j] + (P1[j] - li) * rem
                    d0[j] = v1 if v1 < v2 else v2
                if j >= 1:
                    rem = m - i - (j - 1)
                    rj = R[j - 1]
                    v1 = d1[j - 1] + (rj - P1[j - 1]) * rem
                    v2 = d0[j - 1] + (rj - P0[i]) * rem
                    d1[j] = v1 if v1 < v2 else v2
        return min(dp0[a][b], dp1[a][b])
