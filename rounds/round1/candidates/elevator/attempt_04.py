class Solution:
    def elevatorRequests(self, n: int, start: int, requests: list[int]) -> int:
        a = [0] + sorted(start - x for x in requests if x < start)
        b = [0] + sorted(x - start for x in requests if x > start)
        p = len(a) - 1
        q = len(b) - 1
        m = p + q
        INF = float('inf')
        # row i = 0
        prevL = [INF] * (q + 1)
        prevR = [INF] * (q + 1)
        prevL[0] = 0
        prevR[0] = 0
        for j in range(1, q + 1):
            rem = m - (j - 1)
            prevR[j] = prevR[j - 1] + (b[j] - b[j - 1]) * rem
        for i in range(1, p + 1):
            ai = a[i]
            da = ai - a[i - 1]
            curL = [INF] * (q + 1)
            curR = [INF] * (q + 1)
            base = m - (i - 1)
            for j in range(q + 1):
                rem = base - j
                v1 = prevL[j] + da * rem
                v2 = prevR[j] + (b[j] + ai) * rem
                curL[j] = v1 if v1 < v2 else v2
            base2 = m - i + 1
            for j in range(1, q + 1):
                rem = base2 - j
                bj = b[j]
                v1 = curR[j - 1] + (bj - b[j - 1]) * rem
                v2 = curL[j - 1] + (ai + bj) * rem
                curR[j] = v1 if v1 < v2 else v2
            prevL, prevR = curL, curR
        return min(prevL[q], prevR[q])
