from math import inf


def solve(coins, amount):
    best = [0] + [inf] * amount
    for total in range(1, amount + 1):
        for coin in coins:
            if coin <= total:
                best[total] = min(best[total], best[total - coin] + 1)
    return best[amount] if best[amount] < inf else -1
