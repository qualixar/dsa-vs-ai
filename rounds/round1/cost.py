"""Add up what each round 1 answer cost, from results/cost_per_answer.csv.

  python3 cost.py

The figures are what the agent tool reported for each attempt, in US dollars, at the prices of November 2026.
"""
import csv
import os
import statistics

HERE = os.path.dirname(os.path.abspath(__file__))


def main():
    with open(os.path.join(HERE, "results", "cost_per_answer.csv")) as f:
        rows = list(csv.DictReader(f))
    for problem in ("elevator", "rain"):
        costs = [float(r["cost_usd"]) for r in rows if r["problem"] == problem]
        print(f"{problem}: {len(costs)} answers, total ${sum(costs):.2f}, average {100 * statistics.mean(costs):.1f} cents, "
              f"median {100 * statistics.median(costs):.1f} cents, range {100 * min(costs):.1f} to {100 * max(costs):.1f} cents")


if __name__ == "__main__":
    main()
