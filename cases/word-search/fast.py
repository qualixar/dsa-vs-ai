def solve(board, word):
    rows, cols = len(board), len(board[0])
    def hunt(r, c, i):
        if i == len(word):
            return True
        if not (0 <= r < rows and 0 <= c < cols) or board[r][c] != word[i]:
            return False
        letter, board[r][c] = board[r][c], "#"
        found = hunt(r + 1, c, i + 1) or hunt(r - 1, c, i + 1) or hunt(r, c + 1, i + 1) or hunt(r, c - 1, i + 1)
        board[r][c] = letter
        return found
    return any(hunt(r, c, 0) for r in range(rows) for c in range(cols))
