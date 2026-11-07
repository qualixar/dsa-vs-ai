"""Two wrong answers to hunt. Run the check first; README.md explains both behind a fold."""
from collections import defaultdict, deque


def gut(begin, end, words):
    """Always step to the unused word that is closest to the end word."""
    if end not in words:
        return 0
    word, length, used = begin, 1, {begin}
    while word != end:
        options = [w for w in words if w not in used and sum(x != y for x, y in zip(word, w)) == 1]
        if not options:
            return 0
        word = min(options, key=lambda w: sum(x != y for x, y in zip(w, end)))
        used.add(word)
        length += 1
    return length


# A copy of fast.py with exactly one line changed. Find it.
def planted(begin, end, words):
    if end not in words:
        return 0
    patterns = defaultdict(list)
    for word in words:
        for i in range(len(word)):
            patterns[word[:i] + "*" + word[i + 1:]].append(word)
    seen = {begin}
    queue = deque([(begin, 1)])
    while queue:
        word, length = queue.pop()
        if word == end:
            return length
        for i in range(len(word)):
            for other in patterns[word[:i] + "*" + word[i + 1:]]:
                if other not in seen:
                    seen.add(other)
                    queue.append((other, length + 1))
    return 0
