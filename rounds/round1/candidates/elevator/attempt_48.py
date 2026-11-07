class Solution:
    def elevatorRequests(self, n: int, start: int, requests: list[int]) -> int:
        a = sorted(start - r for r in requests if r < start)
        b = sorted(r - start for r in requests if r > start)
        p, q = len(a), len(b)
        k = p + q
        if k == 0:
            return 0
        a = [0] + a
        b = [0] + b
        INF = float('inf')
        prev0 = None
        prev1 = None
        for i in range(p + 1):
            cur0 = [INF] * (q + 1)
            cur1 = [INF] * (q + 1)
            ai = a[i]
            if i == 0:
                cur0[0] = 0
                cur1[0] = 0
            else:
                d = ai - a[i - 1]
                for j in range(q + 1):
                    rem = k - (i - 1) - j
                    v1 = prev0[j] + d * rem
                    v2 = prev1[j] + (ai + b[j]) * rem
                    cur0[j] = v1 if v1 < v2 else v2
            for j in range(1, q + 1):
                rem = k - i - (j - 1)
                bj = b[j]
                v1 = cur1[j - 1] + (bj - b[j - 1]) * rem
                v2 = cur0[j - 1] + (ai + bj) * rem
                cur1[j] = v1 if v1 < v2 else v2
            prev0, prev1 = cur0, cur1
        return min(prev0[q], prev1[q])
