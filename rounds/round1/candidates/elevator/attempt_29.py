class Solution:
    def elevatorRequests(self, n: int, start: int, requests: list[int]) -> int:
        a = sorted(start - x for x in requests if x < start)
        b = sorted(x - start for x in requests if x > start)
        L, R = len(a), len(b)
        m = L + R
        if m == 0:
            return 0
        a = [0] + a
        b = [0] + b
        INF = float('inf')
        prevL = [INF] * (R + 1)
        prevR = [INF] * (R + 1)
        for i in range(L + 1):
            curL = [INF] * (R + 1)
            curR = [INF] * (R + 1)
            ai = a[i]
            if i == 0:
                curL[0] = 0
                curR[0] = 0
            else:
                d = ai - a[i - 1]
                for j in range(R + 1):
                    rem = m - (i - 1) - j
                    v1 = prevL[j] + d * rem
                    v2 = prevR[j] + (ai + b[j]) * rem
                    curL[j] = v1 if v1 < v2 else v2
            for j in range(1, R + 1):
                rem = m - i - (j - 1)
                bj = b[j]
                v1 = curR[j - 1] + (bj - b[j - 1]) * rem
                v2 = curL[j - 1] + (ai + bj) * rem
                curR[j] = v1 if v1 < v2 else v2
            if i == 0:
                curL = [INF] * (R + 1)
                curL[0] = 0
            prevL, prevR = curL, curR
        return min(prevL[R], prevR[R])
