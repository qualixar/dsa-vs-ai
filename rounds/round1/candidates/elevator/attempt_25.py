class Solution:
    def elevatorRequests(self, n: int, start: int, requests: list[int]) -> int:
        left = sorted(start - r for r in requests if r < start)
        right = sorted(r - start for r in requests if r > start)
        a = [0] + left
        b = [0] + right
        p, q = len(left), len(right)
        m = p + q
        if m == 0:
            return 0
        INF = float('inf')
        prevL = [INF] * (q + 1)
        prevR = [INF] * (q + 1)
        for i in range(p + 1):
            curL = [INF] * (q + 1)
            curR = [INF] * (q + 1)
            ai = a[i]
            ai1 = a[i - 1] if i > 0 else 0
            for j in range(q + 1):
                if i == 0 and j == 0:
                    curL[0] = 0
                    curR[0] = 0
                    continue
                if i > 0:
                    rem = m - (i - 1) - j
                    x = prevL[j] + (ai - ai1) * rem
                    y = prevR[j] + (b[j] + ai) * rem
                    curL[j] = x if x < y else y
                if j > 0:
                    rem = m - i - (j - 1)
                    bj = b[j]
                    x = curR[j - 1] + (bj - b[j - 1]) * rem
                    y = curL[j - 1] + (ai + bj) * rem
                    curR[j] = x if x < y else y
            prevL, prevR = curL, curR
        return min(prevL[q], prevR[q])
