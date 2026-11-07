def solve(coins, amount):
    """Try every count of every coin."""
    def best(i, left):
        if i == len(coins):
            return 0 if left == 0 else -1
        answer = -1
        for n in range(left // coins[i] + 1):
            rest = best(i + 1, left - n * coins[i])
            if rest >= 0 and (answer < 0 or n + rest < answer):
                answer = n + rest
        return answer
    return best(0, amount)
