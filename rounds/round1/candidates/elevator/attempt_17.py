class Solution:
    def elevatorRequests(self, n: int, start: int, requests: list[int]) -> int:
        A = sorted(start - x for x in requests if x < start)
        B = sorted(x - start for x in requests if x > start)
        L, R = len(A), len(B)
        m = L + R
        if m == 0:
            return 0
        a = [0] + A
        b = [0] + B
        INF = float('inf')
        prevL = None
        prevR = None
        for i in range(L + 1):
            curL = [INF] * (R + 1)
            curR = [INF] * (R + 1)
            ai = a[i]
            for j in range(R + 1):
                if i == 0 and j == 0:
                    curL[0] = 0
                    curR[0] = 0
                    continue
                if i > 0:
                    rem = m - (i - 1) - j
                    v1 = prevL[j] + (ai - a[i - 1]) * rem
                    v2 = prevR[j] + (b[j] + ai) * rem
                    curL[j] = v1 if v1 < v2 else v2
                if j > 0:
                    rem = m - i - (j - 1)
                    bj = b[j]
                    v1 = curR[j - 1] + (bj - b[j - 1]) * rem
                    v2 = curL[j - 1] + (ai + bj) * rem
                    curR[j] = v1 if v1 < v2 else v2
            prevL, prevR = curL, curR
        return min(prevL[R], prevR[R])
