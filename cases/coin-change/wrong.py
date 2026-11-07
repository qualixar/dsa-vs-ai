"""Two wrong answers to hunt. Run the check first; README.md explains both behind a fold."""
from math import inf


def gut(coins, amount):
    """Take the largest coin that fits, as many times as it fits, then the next."""
    count = 0
    for coin in sorted(coins, reverse=True):
        count += amount // coin
        amount %= coin
    return count if amount == 0 else -1


# A copy of fast.py with exactly one line changed. Find it.
def planted(coins, amount):
    best = [0] + [inf] * amount
    for total in range(1, amount + 1):
        for coin in coins:
            if coin < total:
                best[total] = min(best[total], best[total - coin] + 1)
    return best[amount] if best[amount] < inf else -1
