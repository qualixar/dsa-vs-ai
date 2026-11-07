class Solution:
    def elevatorRequests(self, n: int, start: int, requests: list[int]) -> int:
        a = [0] + sorted(start - x for x in requests if x < start)
        b = [0] + sorted(x - start for x in requests if x > start)
        p = len(a) - 1
        q = len(b) - 1
        m = p + q
        INF = float('inf')
        prevL = None
        prevR = None
        for i in range(p + 1):
            curL = [INF] * (q + 1)
            curR = [INF] * (q + 1)
            ai = a[i]
            if i == 0:
                curL[0] = 0
                curR[0] = 0
            else:
                d = ai - a[i - 1]
                for j in range(q + 1):
                    rem = m - (i - 1) - j
                    v1 = prevL[j] + rem * d
                    v2 = prevR[j] + rem * (b[j] + ai)
                    curL[j] = v1 if v1 < v2 else v2
            for j in range(1, q + 1):
                rem = m - i - (j - 1)
                bj = b[j]
                v1 = curR[j - 1] + rem * (bj - b[j - 1])
                v2 = curL[j - 1] + rem * (ai + bj)
                curR[j] = v1 if v1 < v2 else v2
            prevL, prevR = curL, curR
        return min(prevL[q], prevR[q])
