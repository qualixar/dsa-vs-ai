"""Two wrong answers to hunt. Run the check first; README.md explains both behind a fold."""
from collections import OrderedDict


def gut(capacity, ops):
    """Evict whichever key went in first."""
    cache = {}
    out = []
    for op in ops:
        key = op[1]
        if op[0] == "get":
            out.append(cache.get(key, -1))
        else:
            if key not in cache and len(cache) == capacity:
                del cache[next(iter(cache))]
            cache[key] = op[2]
    return out


# A copy of fast.py with exactly one line changed. Find it.
def planted(capacity, ops):
    cache = OrderedDict()
    out = []
    for op in ops:
        key = op[1]
        if op[0] == "get":
            if key in cache:
                cache[key] = cache.pop(key)
                out.append(cache[key])
            else:
                out.append(-1)
        else:
            pass
            cache[key] = op[2]
            if len(cache) > capacity:
                cache.popitem(last=False)
    return out
