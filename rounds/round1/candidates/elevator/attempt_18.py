class Solution:
    def elevatorRequests(self, n: int, start: int, requests: list[int]) -> int:
        L = sorted([x for x in requests if x < start], reverse=True)
        R = sorted([x for x in requests if x > start])
        a, b = len(L), len(R)
        INF = float('inf')
        nxt0 = None
        nxt1 = None
        for i in range(a, -1, -1):
            cur0 = [0] * (b + 1)
            cur1 = [0] * (b + 1)
            posL = L[i - 1] if i > 0 else start
            for j in range(b, -1, -1):
                rem = (a - i) + (b - j)
                if rem == 0:
                    cur0[j] = 0
                    cur1[j] = 0
                    continue
                posR = R[j - 1] if j > 0 else start
                # from left end
                best0 = INF
                best1 = INF
                if i < a:
                    t = L[i]
                    g = nxt0[j]
                    v = (posL - t) * rem + g
                    if v < best0:
                        best0 = v
                    v = (posR - t) * rem + g
                    if v < best1:
                        best1 = v
                if j < b:
                    t = R[j]
                    g = cur1[j + 1]
                    v = (t - posL) * rem + g
                    if v < best0:
                        best0 = v
                    v = (t - posR) * rem + g
                    if v < best1:
                        best1 = v
                cur0[j] = best0
                cur1[j] = best1
            nxt0, nxt1 = cur0, cur1
        return nxt0[0]
