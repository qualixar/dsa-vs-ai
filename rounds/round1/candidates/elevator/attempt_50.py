class Solution:
    def elevatorRequests(self, n: int, start: int, requests: list[int]) -> int:
        L = sorted([x for x in requests if x < start], reverse=True)
        R = sorted([x for x in requests if x > start])
        a, b = len(L), len(R)
        lp = [start] + L
        rp = [start] + R
        tot = a + b
        INF = float('inf')
        # row i = 0
        prev0 = [INF] * (b + 1)
        prev1 = [INF] * (b + 1)
        prev0[0] = 0
        prev1[0] = 0
        for j in range(1, b + 1):
            rem = tot - (j - 1)
            prev1[j] = prev1[j - 1] + rem * (rp[j] - rp[j - 1])
        for i in range(1, a + 1):
            cur0 = [INF] * (b + 1)
            cur1 = [INF] * (b + 1)
            li = lp[i]
            dli = lp[i - 1] - li
            for j in range(b + 1):
                rem = tot - (i - 1) - j
                v1 = prev0[j] + rem * dli
                v2 = prev1[j] + rem * (rp[j] - li)
                cur0[j] = v1 if v1 < v2 else v2
                if j > 0:
                    rem2 = tot - i - (j - 1)
                    rj = rp[j]
                    w1 = cur1[j - 1] + rem2 * (rj - rp[j - 1])
                    w2 = cur0[j - 1] + rem2 * (rj - li)
                    cur1[j] = w1 if w1 < w2 else w2
            prev0, prev1 = cur0, cur1
        return int(min(prev0[b], prev1[b]))
