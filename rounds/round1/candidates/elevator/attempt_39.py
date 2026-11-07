class Solution:
    def elevatorRequests(self, n: int, start: int, requests: list[int]) -> int:
        L = sorted([x for x in requests if x < start], reverse=True)
        R = sorted([x for x in requests if x > start])
        p, q = len(L), len(R)
        T = p + q
        posL = [start] + L
        posR = [start] + R
        INF = float('inf')
        # row a = 0
        prevL = [INF] * (q + 1)
        prevR = [INF] * (q + 1)
        prevL[0] = 0
        prevR[0] = 0
        for b in range(1, q + 1):
            rem = T - b + 1
            prevR[b] = prevR[b - 1] + (posR[b] - posR[b - 1]) * rem
        for a in range(1, p + 1):
            curL = [INF] * (q + 1)
            curR = [INF] * (q + 1)
            pa1 = posL[a - 1]
            pa = posL[a]
            d = pa1 - pa
            base = T - a + 1
            for b in range(q + 1):
                rem = base - b
                x = prevL[b] + d * rem
                y = prevR[b] + (posR[b] - pa) * rem
                curL[b] = x if x < y else y
            base2 = T - a + 1
            cl = curL
            cr = curR
            for b in range(1, q + 1):
                rem = base2 - b
                pb = posR[b]
                x = cl[b - 1] + (pb - pa) * rem
                y = cr[b - 1] + (pb - posR[b - 1]) * rem
                cr[b] = x if x < y else y
            prevL, prevR = curL, curR
        return min(prevL[q], prevR[q])
