class Solution:
    def elevatorRequests(self, n: int, start: int, requests: list[int]) -> int:
        L = sorted([x for x in requests if x < start], reverse=True)
        R = sorted([x for x in requests if x > start])
        a, b = len(L), len(R)
        k = a + b
        INF = float('inf')
        pl = [start] + L
        pr = [start] + R
        prevA = None
        prevB = None
        for i in range(a + 1):
            curA = [INF] * (b + 1)
            curB = [INF] * (b + 1)
            if i == 0:
                curA[0] = 0
                curB[0] = 0
            else:
                li = pl[i]
                lprev = pl[i - 1]
                d1 = lprev - li
                base = k - (i - 1)
                for j in range(b + 1):
                    rem = base - j
                    x = prevA[j] + rem * d1
                    y = prevB[j] + rem * (pr[j] - li)
                    curA[j] = x if x < y else y
            # fill B
            pli = pl[i]
            for j in range(1, b + 1):
                rem = k - i - (j - 1)
                rj = pr[j]
                x = curA[j - 1] + rem * (rj - pli)
                y = curB[j - 1] + rem * (rj - pr[j - 1])
                curB[j] = x if x < y else y
            prevA, prevB = curA, curB
        return min(prevA[b], prevB[b])
