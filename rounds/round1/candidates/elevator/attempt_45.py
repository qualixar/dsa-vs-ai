class Solution:
    def elevatorRequests(self, n: int, start: int, requests: list[int]) -> int:
        a = [0] + sorted(start - r for r in requests if r < start)
        b = [0] + sorted(r - start for r in requests if r > start)
        p = len(a) - 1
        q = len(b) - 1
        m = p + q
        if m == 0:
            return 0
        INF = float('inf')
        # i = 0 row
        cur0 = [0] + [INF] * q
        cur1 = [0] * (q + 1)
        for j in range(1, q + 1):
            rem = m - (j - 1)
            v1 = cur1[j - 1] + (b[j] - b[j - 1]) * rem
            v2 = cur0[j - 1] + (b[j] + a[0]) * rem
            cur1[j] = v1 if v1 < v2 else v2
        prev0, prev1 = cur0, cur1
        for i in range(1, p + 1):
            ai = a[i]
            da = ai - a[i - 1]
            cur0 = [INF] * (q + 1)
            cur1 = [INF] * (q + 1)
            base0 = m - (i - 1)
            base1 = m - i
            for j in range(q + 1):
                rem0 = base0 - j
                v1 = prev0[j] + da * rem0
                v2 = prev1[j] + (ai + b[j]) * rem0
                cur0[j] = v1 if v1 < v2 else v2
                if j:
                    rem1 = base1 - (j - 1)
                    w1 = cur1[j - 1] + (b[j] - b[j - 1]) * rem1
                    w2 = cur0[j - 1] + (ai + b[j]) * rem1
                    cur1[j] = w1 if w1 < w2 else w2
            prev0, prev1 = cur0, cur1
        return int(min(prev0[q], prev1[q]))
