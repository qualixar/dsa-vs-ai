"""Input generator for implement-trie-prefix-tree. `generate` makes small inputs for the slow machine; `big` makes one large input for fast, and `big_check` tests the answer to it."""
from checking import strict_equal

TITLE = "Implement Trie (Prefix Tree)"
FAMILY = "Tries"
LEETCODE = (208, "implement-trie-prefix-tree")

MAX_SIZE = 10


def _word(rng):
    return "".join(rng.choice("ab") for _ in range(rng.randint(1, 3)))


def generate(rng, size):
    return ([(rng.choice(("insert", "search", "prefix")), _word(rng)) for _ in range(size)],)


def big(rng):
    ops = []
    for _ in range(100000):
        word = "".join(rng.choice("abcdef") for _ in range(rng.randint(1, 12)))
        ops.append((rng.choice(("insert", "search", "prefix")), word))
    return (ops,)


def big_check(args, got):
    """Two plain sets: the words, and every beginning of every word."""
    words, beginnings = set(), set()
    out = []
    for op, word in args[0]:
        if op == "insert":
            words.add(word)
            beginnings.update(word[:i] for i in range(1, len(word) + 1))
        else:
            out.append(word in words if op == "search" else word in beginnings)
    return strict_equal(got, out)
