"""Scores two finished runs from their reports. Nothing is final until a person has read every
flagged test diff: each verdict names the exact diff it covers, so it can't be reused for another.

  python3 -I score.py run1/final.json run2/final.json --verdicts d1c-verdicts.jsonl

A verdicts file has one JSON object per line:
  {"commit": "...", "file": "tests/x.py", "diff_sha256": "...", "verdict": "harmless", "reason": "..."}
The verdict is "weakening" or "harmless". Exit code 2 means some diff still has no verdict.
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import drift  # noqa: E402


def score(run1, run2, verdicts):
    out = drift.h6(run1, run2)
    out["flagged_test_diffs"] = {}
    unresolved = 0
    for name, run in (("run1", run1), ("run2", run2)):
        read = drift.resolve_d1c(run["events"], verdicts)
        out["flagged_test_diffs"][name] = {k: len(v) for k, v in read.items()}
        unresolved += len(read["unresolved"])
    out["final"] = unresolved == 0
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("run1")
    ap.add_argument("run2")
    ap.add_argument("--verdicts")
    a = ap.parse_args()
    with open(a.run1) as f:
        run1 = json.load(f)
    with open(a.run2) as f:
        run2 = json.load(f)
    verdicts = []
    if a.verdicts:
        with open(a.verdicts) as f:
            verdicts = [json.loads(line) for line in f if line.strip()]
    result = score(run1, run2, verdicts)
    print(json.dumps(result, indent=1))
    sys.exit(0 if result["final"] else 2)


if __name__ == "__main__":
    main()
