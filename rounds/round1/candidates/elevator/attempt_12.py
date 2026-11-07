class Solution:
    def elevatorRequests(self, n: int, start: int, requests: list[int]) -> int:
        left = sorted(start - x for x in requests if x < start)
        right = sorted(x - start for x in requests if x > start)
        p, q = len(left), len(right)
        T = p + q
        if T == 0:
            return 0
        dl = [0] + left
        dr = [0] + right
        INF = float('inf')
        prevL = [INF] * (q + 1)
        prevR = [INF] * (q + 1)
        for i in range(p + 1):
            curL = [INF] * (q + 1)
            curR = [INF] * (q + 1)
            di = dl[i]
            if i == 0:
                curL[0] = 0
                curR[0] = 0
            else:
                step = di - dl[i - 1]
                for j in range(q + 1):
                    rem = T - (i - 1) - j
                    v1 = prevL[j] + step * rem
                    v2 = prevR[j] + (dr[j] + di) * rem
                    curL[j] = v1 if v1 < v2 else v2
            for j in range(1, q + 1):
                rem = T - i - (j - 1)
                v1 = curR[j - 1] + (dr[j] - dr[j - 1]) * rem
                v2 = curL[j - 1] + (di + dr[j]) * rem
                curR[j] = v1 if v1 < v2 else v2
            prevL, prevR = curL, curR
        return min(prevL[q], prevR[q])
