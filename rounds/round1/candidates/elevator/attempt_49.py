class Solution:
    def elevatorRequests(self, n: int, start: int, requests: list[int]) -> int:
        a = [0] + sorted(start - x for x in requests if x < start)
        b = [0] + sorted(x - start for x in requests if x > start)
        L = len(a) - 1
        R = len(b) - 1
        K = L + R
        INF = float('inf')
        prev0 = None
        prev1 = None
        for i in range(L + 1):
            cur0 = [INF] * (R + 1)
            cur1 = [INF] * (R + 1)
            ai = a[i]
            for j in range(R + 1):
                if i == 0 and j == 0:
                    cur0[0] = 0
                    cur1[0] = 0
                    continue
                if i >= 1:
                    rem = K - (i - 1) - j
                    v = prev0[j] + (ai - a[i - 1]) * rem
                    w = prev1[j] + (b[j] + ai) * rem
                    cur0[j] = v if v < w else w
                if j >= 1:
                    rem = K - i - (j - 1)
                    bj = b[j]
                    v = cur1[j - 1] + (bj - b[j - 1]) * rem
                    w = cur0[j - 1] + (ai + bj) * rem
                    cur1[j] = v if v < w else w
            prev0, prev1 = cur0, cur1
        return min(prev0[R], prev1[R])
