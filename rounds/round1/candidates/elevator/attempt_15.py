class Solution:
    def elevatorRequests(self, n: int, start: int, requests: list[int]) -> int:
        left = sorted([x for x in requests if x < start], reverse=True)
        right = sorted([x for x in requests if x > start])
        a, b = len(left), len(right)
        m = a + b
        lpos = [start] + left
        rpos = [start] + right
        INF = float('inf')
        prev0 = [INF] * (b + 1)
        prev1 = [INF] * (b + 1)
        for i in range(a + 1):
            cur0 = [INF] * (b + 1)
            cur1 = [INF] * (b + 1)
            if i == 0:
                cur0[0] = 0
                cur1[0] = 0
            li = lpos[i]
            for j in range(b + 1):
                if i >= 1:
                    rem = m - (i - 1) - j
                    v1 = prev0[j] + (lpos[i - 1] - li) * rem
                    v2 = prev1[j] + (rpos[j] - li) * rem
                    cur0[j] = v1 if v1 < v2 else v2
                if j >= 1:
                    rem = m - i - (j - 1)
                    rj = rpos[j]
                    v1 = cur1[j - 1] + (rj - rpos[j - 1]) * rem
                    v2 = cur0[j - 1] + (rj - li) * rem
                    cur1[j] = v1 if v1 < v2 else v2
            prev0, prev1 = cur0, cur1
        return min(prev0[b], prev1[b])
