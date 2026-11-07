"""Two wrong answers to hunt. Run the check first; README.md explains both behind a fold."""
from collections import deque


def gut(n, prereqs):
    """Do the courses with the fewest prerequisites first."""
    count = [0] * n
    for course, _ in prereqs:
        count[course] += 1
    return sorted(range(n), key=lambda c: count[c])


# A copy of fast.py with exactly one line changed. Find it.
def planted(n, prereqs):
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
    return order
