class Solution:
    def elevatorRequests(self, n: int, start: int, requests: list[int]) -> int:
        reqs = [x for x in requests if x != start]
        l = [0] + sorted(start - x for x in reqs if x < start)
        r = [0] + sorted(x - start for x in reqs if x > start)
        a = len(l) - 1
        b = len(r) - 1
        m = a + b
        if m == 0:
            return 0
        INF = float('inf')
        prev0 = None
        prev1 = None
        for i in range(a + 1):
            cur0 = [INF] * (b + 1)
            cur1 = [INF] * (b + 1)
            li = l[i]
            if i == 0:
                cur0[0] = 0
                cur1[0] = 0
            else:
                d = li - l[i - 1]
                p0 = prev0
                p1 = prev1
                for j in range(b + 1):
                    rem = m - (i - 1) - j
                    v1 = p0[j] + d * rem
                    v2 = p1[j] + (li + r[j]) * rem
                    cur0[j] = v1 if v1 < v2 else v2
            for j in range(1, b + 1):
                rem = m - i - (j - 1)
                v1 = cur1[j - 1] + (r[j] - r[j - 1]) * rem
                v2 = cur0[j - 1] + (li + r[j]) * rem
                cur1[j] = v1 if v1 < v2 else v2
            prev0, prev1 = cur0, cur1
        return min(prev0[b], prev1[b])
