from collections import OrderedDict


def solve(capacity, ops):
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
            cache.pop(key, None)
            cache[key] = op[2]
            if len(cache) > capacity:
                cache.popitem(last=False)
    return out
