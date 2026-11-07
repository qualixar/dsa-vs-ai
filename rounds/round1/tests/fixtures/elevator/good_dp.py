class Solution:
    def elevatorRequests(self, n: int, start: int, requests: list[int]) -> int:
        left = sorted((r for r in requests if r < start), reverse=True)
        right = sorted(r for r in requests if r > start)
        a, b = len(left), len(right)
        k = a + b
        if k == 0:
            return 0
        inf = float("inf")
        L = [[inf] * (b + 1) for _ in range(a + 1)]
        R = [[inf] * (b + 1) for _ in range(a + 1)]
        if a: L[1][0] = (start - left[0]) * k
        if b: R[0][1] = (right[0] - start) * k
        for i in range(a + 1):
            for j in range(b + 1):
                w = k - i - j
                if w == 0: continue
                for cost, pos in ((L[i][j], left[i - 1] if i else None), (R[i][j], right[j - 1] if j else None)):
                    if cost == inf: continue
                    if i < a: L[i + 1][j] = min(L[i + 1][j], cost + (pos - left[i]) * w)
                    if j < b: R[i][j + 1] = min(R[i][j + 1], cost + (right[j] - pos) * w)
        return min(L[a][b], R[a][b])
