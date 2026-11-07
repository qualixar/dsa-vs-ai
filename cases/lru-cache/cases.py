"""Input generator for lru-cache. `generate` makes small inputs for the slow machine; `big` makes one large input for fast, and `big_check` tests the answer to it."""
from checking import strict_equal
from heapq import heapify, heappop, heappush

TITLE = "LRU Cache"
FAMILY = "Linked structures"
LEETCODE = (146, "lru-cache")

MAX_SIZE = 14


def generate(rng, size):
    ops = []
    for _ in range(size):
        key = rng.randint(0, 4)
        ops.append(("get", key) if rng.random() < 0.5 else ("put", key, rng.randint(0, 9)))
    return (rng.randint(1, 3), ops)


def edges():
    return [(1, [("put", -2**31, 2**31 - 1), ("get", -2**31), ("put", 2**31 - 1, -2**31), ("get", 2**31 - 1), ("get", -2**31)])]


def big(rng):
    ops = []
    for _ in range(200000):
        key = rng.randint(0, 5000)
        ops.append(("get", key) if rng.random() < 0.5 else ("put", key, 1))
    return (1000, ops)


def big_check(args, got):
    """Stamp each key with its last use and evict by the oldest stamp, using a heap with stale entries skipped."""
    capacity, ops = args
    value, stamp, heap = {}, {}, []
    out = []
    for now, op in enumerate(ops):
        key = op[1]
        if op[0] == "get":
            out.append(value.get(key, -1))
            if key not in value:
                continue
        else:
            value[key] = op[2]
        stamp[key] = now
        heappush(heap, (now, key))
        while len(value) > capacity:
            when, old = heappop(heap)
            if stamp.get(old) == when:
                del value[old], stamp[old]
    return strict_equal(got, out)
