def solve(n):
    """Write out each number in binary and count the ones."""
    return [bin(i).count("1") for i in range(n + 1)]
