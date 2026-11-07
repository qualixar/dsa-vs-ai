class Solution:
    def elevatorRequests(self, n: int, start: int, requests: list[int]) -> int:
        a = [0] + sorted(start - r for r in requests if r < start)
        b = [0] + sorted(r - start for r in requests if r > start)
        L = len(a) - 1
        R = len(b) - 1
        M = L + R
        INF = float('inf')
        prev0 = None
        prev1 = None
        for i in range(L + 1):
            cur0 = [INF] * (R + 1)
            cur1 = [INF] * (R + 1)
            ai = a[i]
            if i == 0:
                cur0[0] = 0
                cur1[0] = 0
            else:
                d = ai - a[i - 1]
                p0 = prev0
                p1 = prev1
                for j in range(R + 1):
                    rem = M - (i - 1) - j
                    v1 = p0[j] + d * rem
                    v2 = p1[j] + (ai + b[j]) * rem
                    cur0[j] = v1 if v1 < v2 else v2
            for j in range(1, R + 1):
                rem = M - i - (j - 1)
                bj = b[j]
                v1 = cur1[j - 1] + (bj - b[j - 1]) * rem
                v2 = cur0[j - 1] + (ai + bj) * rem
                cur1[j] = v1 if v1 < v2 else v2
            if i > 0:
                cur1[0] = INF
            prev0, prev1 = cur0, cur1
        if L > 0 or R > 0:
            # cur0[0] for i==0 means at start; fine since if L==0 handled
            pass
        res = min(prev0[R], prev1[R])
        return int(res)
