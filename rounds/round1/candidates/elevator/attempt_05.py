class Solution:
    def elevatorRequests(self, n: int, start: int, requests: list[int]) -> int:
        lefts = sorted([x for x in requests if x < start], reverse=True)
        rights = sorted([x for x in requests if x > start])
        p, q = len(lefts), len(rights)
        m = p + q
        if m == 0:
            return 0
        a = [start] + lefts
        b = [start] + rights
        INF = float('inf')
        prev0 = [INF] * (q + 1)
        prev1 = [INF] * (q + 1)
        for i in range(p + 1):
            cur0 = [INF] * (q + 1)
            cur1 = [INF] * (q + 1)
            ai = a[i]
            if i == 0:
                cur0[0] = 0
                cur1[0] = 0
            else:
                api = a[i - 1]
                for j in range(q + 1):
                    rem = m - (i - 1) - j
                    v = prev0[j] + (api - ai) * rem
                    w = prev1[j] + (b[j] - ai) * rem
                    cur0[j] = v if v < w else w
            for j in range(1, q + 1):
                rem = m - i - (j - 1)
                bj = b[j]
                v = cur1[j - 1] + (bj - b[j - 1]) * rem
                w = cur0[j - 1] + (bj - ai) * rem
                cur1[j] = v if v < w else w
            prev0, prev1 = cur0, cur1
        return min(prev0[q], prev1[q])
