"""LeetCode 4023, Elevator Requests II: the fresh 2026 problem
(Biweekly Contest 189 Q4, 15 Aug 2026).

Limits from LeetCode (pulled 4 Nov 2026): 1 <= n <= 10^9,
1 <= requests.length <= 1500, 0 <= start, requests[i] <= n - 1, requests distinct.
"""
import itertools
import random

METHOD = "elevatorRequests"
SEED = 4023_2026


def _cost_of_order(start, order):
    """Follow the targets in this order; any floor passed on the way is served."""
    pos, t, done, total = start, 0, set(), 0
    for target in order:
        if target in done:
            continue
        lo, hi = sorted((pos, target))
        for r in order:
            if r not in done and lo <= r <= hi:
                done.add(r)
                total += t + abs(r - pos)
        t += abs(target - pos)
        pos = target
    return total


def reference(n, start, requests):
    """Slow and obviously correct: try every order of the requests."""
    rest = [r for r in requests if r != start]
    if not rest:
        return 0
    return min(_cost_of_order(start, p) for p in itertools.permutations(rest))


def fast(n, start, requests):
    """Our own O(k^2) solution. The served floors always form one unbroken
    block around the start, so track how many below and above are served
    and which end the lift is on. Moving d floors costs d for every
    request still waiting."""
    left = sorted((r for r in requests if r < start), reverse=True)
    right = sorted(r for r in requests if r > start)
    a, b = len(left), len(right)
    k = a + b
    if k == 0:
        return 0
    inf = float("inf")
    at_left = [[inf] * (b + 1) for _ in range(a + 1)]
    at_right = [[inf] * (b + 1) for _ in range(a + 1)]
    if a:
        at_left[1][0] = (start - left[0]) * k
    if b:
        at_right[0][1] = (right[0] - start) * k
    for i in range(a + 1):
        for j in range(b + 1):
            waiting = k - i - j
            if waiting == 0:
                continue
            for cost, pos in ((at_left[i][j], left[i - 1] if i else None),
                              (at_right[i][j], right[j - 1] if j else None)):
                if cost == inf:
                    continue
                if i < a:
                    c = cost + (pos - left[i]) * waiting
                    if c < at_left[i + 1][j]:
                        at_left[i + 1][j] = c
                if j < b:
                    c = cost + (right[j] - pos) * waiting
                    if c < at_right[i][j + 1]:
                        at_right[i][j + 1] = c
    return min(at_left[a][b], at_right[a][b])


def nearest_first(n, start, requests):
    """The tempting wrong idea: always go to the closest waiting floor."""
    rest = sorted(r for r in requests if r != start)
    order, pos = [], start
    while rest:
        nxt = min(rest, key=lambda r: (abs(r - pos), r))
        order.append(nxt)
        rest.remove(nxt)
        pos = nxt
    return _cost_of_order(start, order)


def examples():
    return [([6, 4, [1, 5]], 6), ([8, 3, [3, 7, 1]], 10), ([10, 5, [0, 2, 9]], 22)]


def edge_cases():
    return [
        [1, 0, [0]],                     # only the start floor
        [10, 4, [4, 5]],                 # start is a request
        [10, 0, [3, 6, 9]],              # everything above
        [10, 9, [0, 4, 8]],              # everything below
        [10, 5, [7]],                    # one request
        [20, 10, [8, 13, 14, 15, 16, 17]],  # nearest-first loses: 47 vs 41
        [10, 5, [4, 6]],                 # adjacent both sides
    ]


def random_cases(count=3000, seed=SEED):
    rng = random.Random(seed)
    cases = []
    for _ in range(count):
        n = rng.randint(1, 30)
        k = rng.randint(1, min(n, 7))
        cases.append([n, rng.randrange(n), rng.sample(range(n), k)])
    return cases


def medium_cases(count=600, seed=SEED):
    """8-60 requests, between the small and the full-size tests; half include the start."""
    rng = random.Random(seed + 2)
    cases = [[10, 5, list(range(10))]]
    for i in range(count - 1):
        k = rng.randint(8, 60)
        n = rng.choice([k, 100, 10_000, 10**9])
        start = rng.randrange(n)
        reqs = rng.sample(range(n), k)
        if i % 2 and start not in reqs:
            reqs[0] = start
        cases.append([n, start, reqs])
    return cases


def scale_cases(seed=SEED):
    rng = random.Random(seed + 1)
    big, k = 10**9, 1500
    near = list(range(500_000 - 750, 500_000)) + list(range(500_001, 500_001 + 750))
    return [
        ("random", [big, rng.randrange(big), rng.sample(range(big), k)]),
        ("one-far-request", [big, 0, [big - 1]]),
        ("start-is-a-request", [big, 777_777, [777_777] + rng.sample(range(big), k - 1)]),
        ("start-bottom", [big, 0, rng.sample(range(1, big), k)]),
        ("start-top", [big, big - 1, rng.sample(range(big - 1), k)]),
        ("dense-around-start", [big, 500_000, near]),
        ("lopsided", [big, 10**8, rng.sample(range(10**8 - 200, 10**8), 200)
                      + rng.sample(range(10**8 + 1, big), k - 200)]),
    ]


def sanity(args, out):
    """Gate 3: every request waits at least its own distance from the start,
    and the best plan is never worse than sweeping one way fully, then back."""
    n, start, requests = args
    if not isinstance(out, int) or isinstance(out, bool):
        return "answer is not an integer"
    lower = sum(abs(r - start) for r in requests)
    down_first = _cost_of_order(start, sorted(requests, reverse=True) + sorted(requests))
    up_first = _cost_of_order(start, sorted(requests) + sorted(requests, reverse=True))
    if out < lower:
        return f"below the lower bound {lower}"
    if out > min(down_first, up_first):
        return "worse than a simple sweep"
    return None
