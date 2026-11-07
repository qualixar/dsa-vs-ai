def solve(ops):
    """Keep a plain list of words and scan it for each question."""
    words = []
    out = []
    for op, word in ops:
        if op == "insert":
            words.append(word)
        elif op == "search":
            out.append(any(w == word for w in words))
        else:
            out.append(any(w.startswith(word) for w in words))
    return out
