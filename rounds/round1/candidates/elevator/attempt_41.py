class Solution:
    def elevatorRequests(self, n: int, start: int, requests: list[int]) -> int:
        a = sorted([x for x in requests if x < start], reverse=True)
        b = sorted([x for x in requests if x > start])
        m = len(a) + len(b)
        if m == 0:
            return 0
        INF = float('inf')
        pl = [start] + a
        pr = [start] + b
        A, B = len(a), len(b)
        prevL = prevR = None
        for i in range(A + 1):
            curL = [INF] * (B + 1)
            curR = [INF] * (B + 1)
            if i == 0:
                curL[0] = 0
                curR[0] = 0
            else:
                pli = pl[i]
                dl = pl[i - 1] - pli
                base = m - i + 1
                for j in range(B + 1):
                    rem = base - j
                    v1 = prevL[j] + rem * dl
                    v2 = prevR[j] + rem * (pr[j] - pli)
                    curL[j] = v1 if v1 < v2 else v2
            pli = pl[i]
            base = m - i + 1
            for j in range(1, B + 1):
                rem = base - j
                prj = pr[j]
                v1 = curL[j - 1] + rem * (prj - pli)
                v2 = curR[j - 1] + rem * (prj - pr[j - 1])
                curR[j] = v1 if v1 < v2 else v2
            prevL, prevR = curL, curR
        return min(prevL[B], prevR[B])
