class Solution:
    def elevatorRequests(self, n: int, start: int, requests: list[int]) -> int:
        a = [start] + sorted([x for x in requests if x < start], reverse=True)
        b = [start] + sorted([x for x in requests if x > start])
        p = len(a) - 1
        q = len(b) - 1
        m = p + q
        if m == 0:
            return 0
        INF = float('inf')
        prev0 = None
        prev1 = None
        for i in range(p + 1):
            cur0 = [INF] * (q + 1)
            cur1 = [INF] * (q + 1)
            ai = a[i]
            for j in range(q + 1):
                if i == 0 and j == 0:
                    cur0[0] = 0
                    cur1[0] = 0
                    continue
                if i > 0:
                    rem = m - i + 1 - j
                    v1 = prev0[j] + (a[i - 1] - ai) * rem
                    v2 = prev1[j] + (b[j] - ai) * rem
                    cur0[j] = v1 if v1 < v2 else v2
                if j > 0:
                    rem = m - i - j + 1
                    bj = b[j]
                    v1 = cur1[j - 1] + (bj - b[j - 1]) * rem
                    v2 = cur0[j - 1] + (bj - ai) * rem
                    cur1[j] = v1 if v1 < v2 else v2
            prev0, prev1 = cur0, cur1
        return min(prev0[q], prev1[q])
