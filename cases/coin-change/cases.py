"""Input generator for coin-change. `generate` makes small inputs for the slow machine; `big` makes one large input for fast, and `big_check` tests the answer to it."""
from checking import strict_equal

TITLE = "Coin Change"
FAMILY = "DP: 1D"
LEETCODE = (322, "coin-change")

MAX_SIZE = 4


def generate(rng, size):
    coins = rng.sample(range(1, 13), size + 1)
    return (coins, rng.randint(0, 30))


def big(rng):
    return (rng.sample(range(1, 500), 60), 20000)


def big_check(args, got):
    """Breadth-first search over amounts: the first time the amount is reached is the fewest coins."""
    coins, amount = args
    seen = {0}
    level = [0]
    steps = 0
    while level and amount not in seen:
        steps += 1
        following = []
        for total in level:
            for coin in coins:
                if total + coin <= amount and total + coin not in seen:
                    seen.add(total + coin)
                    following.append(total + coin)
        level = following
    return strict_equal(got, steps if amount in seen else -1)
