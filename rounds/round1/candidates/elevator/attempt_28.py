class Solution:
    def elevatorRequests(self, n: int, start: int, requests: list[int]) -> int:
        l = sorted(start - x for x in requests if x < start)
        r = sorted(x - start for x in requests if x > start)
        a, b = len(l), len(r)
        m = a + b
        if m == 0:
            return 0
        INF = float('inf')
        prevL = [INF] * (b + 1)
        prevR = [INF] * (b + 1)
        for i in range(a + 1):
            curL = [INF] * (b + 1)
            curR = [INF] * (b + 1)
            for j in range(b + 1):
                if i == 0 and j == 0:
                    continue
                if i >= 1:
                    rem = m - (i - 1) - j
                    li = l[i - 1]
                    if i == 1 and j == 0:
                        best = li * m
                    else:
                        best = INF
                        if i >= 2:
                            best = prevL[j] + (li - l[i - 2]) * rem
                        if j >= 1:
                            v = prevR[j] + (r[j - 1] + li) * rem
                            if v < best:
                                best = v
                    curL[j] = best
                if j >= 1:
                    rem = m - i - (j - 1)
                    rj = r[j - 1]
                    if j == 1 and i == 0:
                        best = rj * m
                    else:
                        best = INF
                        if j >= 2:
                            best = curR[j - 1] + (rj - r[j - 2]) * rem
                        if i >= 1:
                            v = curL[j - 1] + (l[i - 1] + rj) * rem
                            if v < best:
                                best = v
                    curR[j] = best
            prevL, prevR = curL, curR
        return min(prevL[b], prevR[b])
