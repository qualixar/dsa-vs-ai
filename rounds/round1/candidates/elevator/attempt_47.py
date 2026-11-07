class Solution:
    def elevatorRequests(self, n: int, start: int, requests: list[int]) -> int:
        left = sorted([x for x in requests if x < start], reverse=True)
        right = sorted([x for x in requests if x > start])
        L, R = len(left), len(right)
        m = L + R
        INF = float('inf')
        lp = [start] + left
        rp = [start] + right
        # row i=0
        prevA = [INF] * (R + 1)
        prevB = [INF] * (R + 1)
        prevA[0] = 0
        prevB[0] = 0
        for j in range(1, R + 1):
            rem = m - (j - 1)
            d = rp[j] - rp[j - 1]
            prevB[j] = prevB[j - 1] + rem * d
        for i in range(1, L + 1):
            curA = [INF] * (R + 1)
            curB = [INF] * (R + 1)
            li = lp[i]
            dl = lp[i - 1] - li
            for j in range(R + 1):
                rem = m - (i - 1) - j
                a = prevA[j] + rem * dl
                b = prevB[j] + rem * (rp[j] - li)
                curA[j] = a if a < b else b
            for j in range(1, R + 1):
                rem = m - i - (j - 1)
                rj = rp[j]
                b = curB[j - 1] + rem * (rj - rp[j - 1])
                a = curA[j - 1] + rem * (rj - li)
                curB[j] = a if a < b else b
            prevA, prevB = curA, curB
        return min(prevA[R], prevB[R])
