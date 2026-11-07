class Solution:
    def elevatorRequests(self, n: int, start: int, requests: list[int]) -> int:
        a = sorted(start - x for x in requests if x < start)
        b = sorted(x - start for x in requests if x > start)
        L, R = len(a), len(b)
        K = L + R
        a = [0] + a
        b = [0] + b
        INF = float('inf')
        prev0 = [0] + [INF] * R
        prev1 = [0] * (R + 1)
        for j in range(1, R + 1):
            prev1[j] = prev1[j - 1] + (K - (j - 1)) * (b[j] - b[j - 1])
        for i in range(1, L + 1):
            ai = a[i]
            d = ai - a[i - 1]
            cur0 = [0] * (R + 1)
            cur1 = [0] * (R + 1)
            cur1[0] = INF
            base = K - (i - 1)
            for j in range(R + 1):
                rem = base - j
                bj = b[j]
                x = prev0[j] + rem * d
                y = prev1[j] + rem * (ai + bj)
                cur0[j] = x if x < y else y
                if j:
                    rem2 = K - i - j + 1
                    x = cur1[j - 1] + rem2 * (bj - b[j - 1])
                    y = cur0[j - 1] + rem2 * (ai + bj)
                    cur1[j] = x if x < y else y
            prev0, prev1 = cur0, cur1
        return min(prev0[R], prev1[R])
