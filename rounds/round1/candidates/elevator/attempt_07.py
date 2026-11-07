class Solution:
    def elevatorRequests(self, n: int, start: int, requests: list[int]) -> int:
        A = sorted(start - r for r in requests if r < start)
        B = sorted(r - start for r in requests if r > start)
        LA, LB = len(A), len(B)
        k = LA + LB
        if k == 0:
            return 0
        a = [0] + A
        b = [0] + B
        INF = float('inf')
        cur0 = [INF] * (LB + 1)
        cur1 = [INF] * (LB + 1)
        cur0[0] = 0
        cur1[0] = 0
        for i in range(LA + 1):
            nxt0 = [INF] * (LB + 1)
            ai = a[i]
            ai1 = a[i + 1] if i < LA else 0
            for j in range(LB + 1):
                rem = k - i - j
                if rem == 0:
                    continue
                v0 = cur0[j]
                v1 = cur1[j]
                bj = b[j]
                if j < LB:
                    bj1 = b[j + 1]
                    c = v0 + rem * (ai + bj1)
                    d = v1 + rem * (bj1 - bj)
                    if d < c:
                        c = d
                    if c < cur1[j + 1]:
                        cur1[j + 1] = c
                if i < LA:
                    c = v0 + rem * (ai1 - ai)
                    d = v1 + rem * (bj + ai1)
                    if d < c:
                        c = d
                    if c < nxt0[j]:
                        nxt0[j] = c
            if i == LA:
                return min(cur0[LB], cur1[LB])
            cur0 = nxt0
            cur1 = [INF] * (LB + 1)
