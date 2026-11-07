def solve(s):
    closers = {")": "(", "]": "[", "}": "{"}
    stack = []
    for c in s:
        if c in closers:
            if not stack or stack.pop() != closers[c]:
                return False
        else:
            stack.append(c)
    return not stack
