class Solution:
    def elevatorRequests(self, n: int, start: int, requests: list[int]) -> int:
        L = sorted([x for x in requests if x < start], reverse=True)
        R = sorted([x for x in requests if x > start])
        a, b = len(L), len(R)
        m = a + b
        if m == 0:
            return 0
        INF = float('inf')
        A = [[INF] * (b + 1) for _ in range(a + 1)]
        B = [[INF] * (b + 1) for _ in range(a + 1)]
        for i in range(a + 1):
            Ai = A[i]
            Bi = B[i]
            Ap = A[i - 1] if i >= 1 else None
            Bp = B[i - 1] if i >= 1 else None
            for j in range(b + 1):
                if i == 0 and j == 0:
                    continue
                if i >= 1:
                    rem = m - (i - 1) - j
                    li = L[i - 1]
                    if i == 1 and j == 0:
                        v = (start - li) * rem
                    else:
                        v = INF
                        if i >= 2:
                            t = Ap[j] + (L[i - 2] - li) * rem
                            if t < v:
                                v = t
                        if j >= 1:
                            t = Bp[j] + (R[j - 1] - li) * rem
                            if t < v:
                                v = t
                    Ai[j] = v
                if j >= 1:
                    rem = m - i - (j - 1)
                    rj = R[j - 1]
                    if j == 1 and i == 0:
                        v = (rj - start) * rem
                    else:
                        v = INF
                        if j >= 2:
                            t = Bi[j - 1] + (rj - R[j - 2]) * rem
                            if t < v:
                                v = t
                        if i >= 1:
                            t = Ai[j - 1] + (rj - L[i - 1]) * rem
                            if t < v:
                                v = t
                    Bi[j] = v
        return min(A[a][b], B[a][b])
