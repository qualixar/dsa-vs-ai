"""Two wrong answers to hunt. Run the check first; README.md explains both behind a fold."""
from heapq import heappush, heapreplace


def gut(meetings):
    """The meeting that clashes with the most others, plus one."""
    best = 0
    for i, (a, b) in enumerate(meetings):
        clashes = sum(1 for j, (c, d) in enumerate(meetings) if j != i and a < d and c < b)
        best = max(best, clashes + 1)
    return best


# A copy of fast.py with exactly one line changed. Find it.
def planted(meetings):
    rooms = []
    for start, end in sorted(meetings):
        if rooms and rooms[0] < start:
            heapreplace(rooms, end)
        else:
            heappush(rooms, end)
    return len(rooms)
