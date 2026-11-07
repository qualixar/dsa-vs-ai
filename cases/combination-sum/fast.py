def solve(candidates, target):
    out = []
    picked = []
    def walk(start, left):
        if left == 0:
            out.append(picked[:])
            return
        for i in range(start, len(candidates)):
            if candidates[i] <= left:
                picked.append(candidates[i])
                walk(i, left - candidates[i])
                picked.pop()
    walk(0, target)
    return out
