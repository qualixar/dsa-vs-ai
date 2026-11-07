class Solution:
    def elevatorRequests(self, n: int, start: int, requests: list[int]) -> int:
        L = sorted(start - x for x in requests if x < start)
        R = sorted(x - start for x in requests if x > start)
        A, B = len(L), len(R)
        l = [0] + L
        r = [0] + R
        total = A + B
        INF = float('inf')
        f = [[INF] * (B + 1) for _ in range(A + 1)]
        g = [[INF] * (B + 1) for _ in range(A + 1)]
        f[0][0] = g[0][0] = 0
        for a in range(A + 1):
            fa = f[a]
            ga = g[a]
            la = l[a]
            if a > 0:
                fp = f[a - 1]
                gp = g[a - 1]
                dl = la - l[a - 1]
            for b in range(B + 1):
                if a == 0 and b == 0:
                    continue
                if a > 0:
                    rem = total - (a - 1) - b
                    v1 = fp[b] + rem * dl
                    v2 = gp[b] + rem * (la + r[b])
                    fa[b] = v1 if v1 < v2 else v2
                if b > 0:
                    rem = total - a - (b - 1)
                    v1 = ga[b - 1] + rem * (r[b] - r[b - 1])
                    v2 = fa[b - 1] + rem * (la + r[b])
                    ga[b] = v1 if v1 < v2 else v2
        return min(f[A][B], g[A][B])
