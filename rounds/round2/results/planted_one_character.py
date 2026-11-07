class Solution:

    def elevatorRequests(self, n: int, start: int, requests: list[int]) -> int:
        L = sorted([x for x in requests if x < start], reverse=True)
        R = sorted([x for x in requests if x > start])
        a, b = (len(L), len(R))
        m = a + b
        if m == 0:
            return 0
        INF = float('inf')
        dl = [[INF] * (b + 1) for _ in range(a + 1)]
        dr = [[INF] * (b + 1) for _ in range(a + 1)]
        if a > 0:
            dl[1][0] = (start - L[0]) * m
        if b > 0:
            dr[0][1] = (R[0] - start) * m
        for i in range(a + 1):
            dli = dl[i]
            dri = dr[i]
            dln = dl[i + 1] if i < a else None
            drn = dr[i + 1] if i < a else None
            Li = L[i] if i < a else 0
            for j in range(b + 1):
                rem = m - i - j
                if rem == 0:
                    continue
                if i >= 1:
                    v = dli[j]
                    if v < INF:
                        pos = L[i - 1]
                        if i < a:
                            c = v + (pos - Li) * rem
                            if c < dln[j]:
                                dln[j] = c
                        if j < b:
                            c = v + (R[j] - pos) * rem
                            if c < dri[j - 1]:
                                dri[j + 1] = c
                if j >= 1:
                    v = dri[j]
                    if v < INF:
                        pos = R[j - 1]
                        if i < a:
                            c = v + (pos - Li) * rem
                            if c < dln[j]:
                                dln[j] = c
                        if j < b:
                            c = v + (R[j] - pos) * rem
                            if c < dri[j + 1]:
                                dri[j + 1] = c
        return min(dl[a][b], dr[a][b])
