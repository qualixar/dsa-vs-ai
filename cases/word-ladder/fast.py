from collections import defaultdict, deque


def solve(begin, end, words):
    if end not in words:
        return 0
    patterns = defaultdict(list)
    for word in words:
        for i in range(len(word)):
            patterns[word[:i] + "*" + word[i + 1:]].append(word)
    seen = {begin}
    queue = deque([(begin, 1)])
    while queue:
        word, length = queue.popleft()
        if word == end:
            return length
        for i in range(len(word)):
            for other in patterns[word[:i] + "*" + word[i + 1:]]:
                if other not in seen:
                    seen.add(other)
                    queue.append((other, length + 1))
    return 0
