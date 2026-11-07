class Solution:
    def elevatorRequests(self, n: int, start: int, requests: list[int]) -> int:
        L = sorted([x for x in requests if x < start], reverse=True)
        R = sorted([x for x in requests if x > start])
        A, B = len(L), len(R)
        m = A + B
        if m == 0:
            return 0
        INF = float('inf')
        prevL = [INF] * (B + 1)
        prevR = [INF] * (B + 1)
        # row i = 0
        curL = [INF] * (B + 1)
        curR = [INF] * (B + 1)
        for j in range(1, B + 1):
            rem = m - (j - 1)
            if j == 1:
                curR[j] = (R[0] - start) * m
            else:
                curR[j] = curR[j - 1] + (R[j - 1] - R[j - 2]) * rem
        prevL, prevR = curL, curR
        for i in range(1, A + 1):
            curL = [INF] * (B + 1)
            curR = [INF] * (B + 1)
            li = L[i - 1]
            for j in range(0, B + 1):
                rem = m - (i - 1) - j
                best = INF
                if i == 1 and j == 0:
                    best = (start - li) * m
                else:
                    if i >= 2:
                        v = prevL[j]
                        if v != INF:
                            v += (L[i - 2] - li) * rem
                            if v < best:
                                best = v
                    if j >= 1:
                        v = prevR[j]
                        if v != INF:
                            v += (R[j - 1] - li) * rem
                            if v < best:
                                best = v
                curL[j] = best
                if j >= 1:
                    rj = R[j - 1]
                    rem2 = m - i - (j - 1)
                    best = INF
                    v = curL[j - 1]
                    if v != INF:
                        best = v + (rj - L[i - 1]) * rem2
                    if j >= 2:
                        v = curR[j - 1]
                        if v != INF:
                            v += (rj - R[j - 2]) * rem2
                            if v < best:
                                best = v
                    curR[j] = best
            prevL, prevR = curL, curR
        return int(min(prevL[B], prevR[B]))
