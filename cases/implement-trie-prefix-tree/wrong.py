"""Two wrong answers to hunt. Run the check first; README.md explains both behind a fold."""


def gut(ops):
    """A list of words, where a prefix question asks whether the text appears inside a word."""
    words = []
    out = []
    for op, word in ops:
        if op == "insert":
            words.append(word)
        elif op == "search":
            out.append(word in words)
        else:
            out.append(any(word in w for w in words))
    return out


# A copy of fast.py with exactly one line changed. Find it.
def planted(ops):
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
            out.append(found)
    return out
