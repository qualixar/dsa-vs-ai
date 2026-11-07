class Solution:
    def elevatorRequests(self, n: int, start: int, requests: list[int]) -> int:
        left = sorted(start - r for r in requests if r < start)
        right = sorted(r - start for r in requests if r > start)
        p, q = len(left), len(right)
        a = [0] + left
        b = [0] + right
        T = p + q
        INF = float('inf')
        prevL = prevR = None
        for i in range(p + 1):
            curL = [INF] * (q + 1)
            curR = [INF] * (q + 1)
            ai = a[i]
            for j in range(q + 1):
                if i == 0 and j == 0:
                    curL[0] = 0
                    curR[0] = 0
                    continue
                if i > 0:
                    c = T - (i - 1) - j
                    v1 = prevL[j] + (ai - a[i - 1]) * c
                    v2 = prevR[j] + (ai + b[j]) * c
                    curL[j] = v1 if v1 < v2 else v2
                if j > 0:
                    c2 = T - i - (j - 1)
                    v1 = curR[j - 1] + (b[j] - b[j - 1]) * c2
                    v2 = curL[j - 1] + (ai + b[j]) * c2
                    curR[j] = v1 if v1 < v2 else v2
            prevL, prevR = curL, curR
        return min(prevL[q], prevR[q])
