class Solution:
    def elevatorRequests(self, n: int, start: int, requests: list[int]) -> int:
        left = sorted([x for x in requests if x < start], reverse=True)
        right = sorted([x for x in requests if x > start])
        a, b = len(left), len(right)
        m = a + b
        if m == 0:
            return 0
        L = [start] + left
        R = [start] + right
        INF = float('inf')
        # row i = 0
        prev0 = [INF] * (b + 1)
        prev1 = [INF] * (b + 1)
        prev0[0] = 0
        prev1[0] = 0
        for j in range(1, b + 1):
            rem = m - j + 1
            prev1[j] = prev1[j - 1] + (R[j] - R[j - 1]) * rem
        for i in range(1, a + 1):
            cur0 = [INF] * (b + 1)
            cur1 = [INF] * (b + 1)
            Li = L[i]
            dL = L[i - 1] - Li
            base = m - i + 1
            for j in range(b + 1):
                rem = base - j
                x = prev0[j] + dL * rem
                y = prev1[j] + (R[j] - Li) * rem
                c0 = x if x < y else y
                cur0[j] = c0
                if j:
                    x = cur1[j - 1] + (R[j] - R[j - 1]) * rem
                    y = c0p + (R[j] - Li) * rem
                    cur1[j] = x if x < y else y
                c0p = c0
            prev0, prev1 = cur0, cur1
        return min(prev0[b], prev1[b])
