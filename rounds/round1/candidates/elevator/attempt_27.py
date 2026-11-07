class Solution:
    def elevatorRequests(self, n: int, start: int, requests: list[int]) -> int:
        L = sorted([x for x in requests if x < start], reverse=True)
        R = sorted([x for x in requests if x > start])
        A, B = len(L), len(R)
        K = A + B
        if K == 0:
            return 0
        INF = float('inf')
        pL = [start] + L
        pR = [start] + R
        # row a=0
        prevL = [INF] * (B + 1)
        prevL[0] = 0
        prevR = [INF] * (B + 1)
        prevR[0] = 0
        for b in range(1, B + 1):
            c = K - b + 1
            v1 = prevR[b - 1] + c * (pR[b] - pR[b - 1])
            v2 = prevL[b - 1] + c * (pR[b] - pL[0])
            prevR[b] = v1 if v1 < v2 else v2
        for a in range(1, A + 1):
            curL = [INF] * (B + 1)
            curR = [INF] * (B + 1)
            pa = pL[a]
            dl = pL[a - 1] - pa
            base = K - a + 1
            for b in range(0, B + 1):
                c = base - b
                v1 = prevL[b] + c * dl
                v2 = prevR[b] + c * (pR[b] - pa)
                curL[b] = v1 if v1 < v2 else v2
                if b > 0:
                    pb = pR[b]
                    v1 = curR[b - 1] + c * (pb - pR[b - 1])
                    v2 = curL[b - 1] + c * (pb - pa)
                    curR[b] = v1 if v1 < v2 else v2
            prevL, prevR = curL, curR
        return min(prevL[B], prevR[B])
