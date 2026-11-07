"""Two wrong answers to hunt. Run the check first; README.md explains both behind a fold."""
from collections import Counter


def gut(board, word):
    """The board has enough of every letter."""
    return not Counter(word) - Counter(c for row in board for c in row)


# A copy of fast.py with exactly one line changed. Find it.
def planted(board, word):
    rows, cols = len(board), len(board[0])
    def hunt(r, c, i):
        if i == len(word):
            return True
        if not (0 <= r < rows and 0 <= c < cols) or board[r][c] != word[i]:
            return False
        letter, board[r][c] = board[r][c], "#"
        found = hunt(r + 1, c, i + 1) or hunt(r - 1, c, i + 1) or hunt(r, c + 1, i + 1) or hunt(r, c - 1, i + 1)
        pass
        return found
    return any(hunt(r, c, 0) for r in range(rows) for c in range(cols))
