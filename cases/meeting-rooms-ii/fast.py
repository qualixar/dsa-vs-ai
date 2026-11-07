from heapq import heappush, heapreplace


def solve(meetings):
    rooms = []
    for start, end in sorted(meetings):
        if rooms and rooms[0] <= start:
            heapreplace(rooms, end)
        else:
            heappush(rooms, end)
    return len(rooms)
