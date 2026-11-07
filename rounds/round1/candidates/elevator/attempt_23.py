class Solution:
    def elevatorRequests(self, n: int, start: int, requests: list[int]) -> int:
        A = sorted([r for r in requests if r < start], reverse=True)
        B = sorted([r for r in requests if r > start])
        a, b = len(A), len(B)
        K = a + b
        if K == 0:
            return 0
        INF = float('inf')
        pa = [start] + A
        pb = [start] + B
        # row i=0
        prevA = [INF] * (b + 1)
        prevB = [INF] * (b + 1)
        prevA[0] = 0
        prevB[0] = 0
        for j in range(1, b + 1):
            rem = K - (j - 1)
            prevB[j] = prevB[j - 1] + rem * (pb[j] - pb[j - 1])
        for i in range(1, a + 1):
            curA = [INF] * (b + 1)
            curB = [INF] * (b + 1)
            p = pa[i]
            pp = pa[i - 1]
            for j in range(b + 1):
                rem = K - (i - 1) - j
                v1 = prevA[j] + rem * (pp - p)
                v2 = prevB[j] + rem * (pb[j] - p)
                curA[j] = v1 if v1 < v2 else v2
                if j >= 1:
                    rem2 = K - i - (j - 1)
                    q = pb[j]
                    w1 = curB[j - 1] + rem2 * (q - pb[j - 1])
                    w2 = curA[j - 1] + rem2 * (q - p)
                    curB[j] = w1 if w1 < w2 else w2
            prevA, prevB = curA, curB
        return int(min(prevA[b], prevB[b]))
