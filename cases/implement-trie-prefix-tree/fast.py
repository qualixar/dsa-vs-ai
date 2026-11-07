def solve(ops):
    root = {}
    out = []
    for op, word in ops:
        node = root
        if op == "insert":
            for c in word:
                node = node.setdefault(c, {})
            node["$"] = True
        else:
            found = True
            for c in word:
                if c not in node:
                    found = False
                    break
                node = node[c]
            out.append(found if op == "prefix" else found and "$" in node)
    return out
