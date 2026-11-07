"""Summarise graded results: survivors per gate with 95% Wilson intervals.

Usage: python3 -I report.py results/rain.json results/elevator.json
Writes a CSV next to each JSON and prints a table.
"""
import csv
import json
import math
import os
import sys

GATES = ("examples", "correctness", "scale", "sanity")


def wilson(k, n, z=1.96):
    if n == 0:
        return (None, None)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0.0, c - h), min(1.0, c + h))


def summarise(path):
    data = json.load(open(path))
    recs = data["records"]
    n = len(recs)
    rows = []
    alive = n
    for g in GATES:
        out = sum(1 for r in recs if r["first_fail"] == g)
        alive -= out
        lo, hi = wilson(alive, n)
        rows.append({"problem": data["problem"], "after_gate": g, "survivors": alive, "of": n,
                     "ci95_low": None if lo is None else round(lo, 3),
                     "ci95_high": None if hi is None else round(hi, 3), "out_here": out})
    with open(os.path.splitext(path)[0] + ".csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    return rows


def main():
    for path in sys.argv[1:]:
        for r in summarise(path):
            ci = "n/a" if r["ci95_low"] is None else f"{r['ci95_low']:.0%}-{r['ci95_high']:.0%}"
            print(f"{r['problem']:9s} after {r['after_gate']:12s} {r['survivors']:3d}/{r['of']}"
                  f"  (95% CI {ci})  out here: {r['out_here']}")


if __name__ == "__main__":
    main()
