class Solution:
    def elevatorRequests(self, n: int, start: int, requests: list[int]) -> int:
        A = sorted([x for x in requests if x < start], reverse=True)
        B = sorted([x for x in requests if x > start])
        a, b = len(A), len(B)
        K = a + b
        if K == 0:
            return 0
        INF = float('inf')
        PA = [start] + A
        PB = [start] + B
        prevL = [INF] * (b + 1)
        prevR = [INF] * (b + 1)
        prevL[0] = 0
        prevR[0] = 0
        # row i = 0: compute R along j
        for j in range(1, b + 1):
            r = K - (j - 1)
            prevR[j] = prevR[j - 1] + r * (PB[j] - PB[j - 1])
        for i in range(1, a + 1):
            pa_prev = PA[i - 1]
            pa = PA[i]
            d = pa_prev - pa
            curL = [0] * (b + 1)
            curR = [INF] * (b + 1)
            base = K - (i - 1)
            for j in range(b + 1):
                r = base - j
                x = prevL[j] + r * d
                y = prevR[j] + r * (PB[j] - pa)
                curL[j] = x if x < y else y
            base2 = K - i + 1
            for j in range(1, b + 1):
                r = base2 - j
                pb = PB[j]
                x = curR[j - 1] + r * (pb - PB[j - 1])
                y = curL[j - 1] + r * (pb - pa)
                curR[j] = x if x < y else y
            prevL, prevR = curL, curR
        if a == 0:
            return prevR[b]
        if b == 0:
            return prevL[b]
        return min(prevL[b], prevR[b])
