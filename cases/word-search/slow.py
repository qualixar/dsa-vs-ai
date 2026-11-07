def solve(board, word):
    """Walk every path of the right length, then read it."""
    rows, cols = len(board), len(board[0])
    def walk(r, c, path):
        path = path + [(r, c)]
        if len(path) == len(word):
            return "".join(board[x][y] for x, y in path) == word
        for x, y in ((r + 1, c), (r - 1, c), (r, c + 1), (r, c - 1)):
            if 0 <= x < rows and 0 <= y < cols and (x, y) not in path and walk(x, y, path):
                return True
        return False
    return any(walk(r, c, []) for r in range(rows) for c in range(cols))
