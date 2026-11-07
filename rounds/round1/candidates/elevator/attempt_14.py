class Solution:
    def elevatorRequests(self, n: int, start: int, requests: list[int]) -> int:
        a = sorted(start - x for x in requests if x < start)
        b = sorted(x - start for x in requests if x > start)
        L, R = len(a), len(b)
        m = L + R
        if m == 0:
            return 0
        a = [0] + a
        b = [0] + b
        INF = float('inf')
        # prev rows for i-1
        prev0 = [INF] * (R + 1)
        prev1 = [INF] * (R + 1)
        prev0[0] = 0
        prev1[0] = 0
        # row i = 0
        for j in range(1, R + 1):
            rem = m - (j - 1)
            prev1[j] = prev1[j - 1] + (b[j] - b[j - 1]) * rem
        for i in range(1, L + 1):
            cur0 = [INF] * (R + 1)
            cur1 = [INF] * (R + 1)
            ai = a[i]
            da = ai - a[i - 1]
            for j in range(R + 1):
                rem = m - (i - 1) - j
                v = prev0[j] + da * rem
                w = prev1[j] + (b[j] + ai) * rem
                cur0[j] = v if v < w else w
                if j >= 1:
                    rem2 = m - i - (j - 1)
                    v = cur1[j - 1] + (b[j] - b[j - 1]) * rem2
                    w = cur0[j - 1] + (ai + b[j]) * rem2
                    cur1[j] = v if v < w else w
            prev0, prev1 = cur0, cur1
        return min(prev0[R], prev1[R])
