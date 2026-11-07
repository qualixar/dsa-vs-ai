from collections import deque


def solve(n, prereqs):
    after = [[] for _ in range(n)]
    waiting = [0] * n
    for course, need in prereqs:
        after[need].append(course)
        waiting[course] += 1
    ready = deque(i for i in range(n) if waiting[i] == 0)
    order = []
    while ready:
        course = ready.popleft()
        order.append(course)
        for other in after[course]:
            waiting[other] -= 1
            if waiting[other] == 0:
                ready.append(other)
    return order if len(order) == n else []
