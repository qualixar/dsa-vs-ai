"""Round 2 checks. No AI is called: they use the 50 elevator solutions in round1/candidates/elevator and the public spec.

A. Wrong strategies a person might write by gut, against the checks.
B. How fast "try every order" dies: real timings on this machine, plus digit counts.
C. Planted changes: one small change at a time in the AI's real solutions, then which layer of checking notices.

Usage: python3 -I rounds/round2/checks.py OUT_DIR [changes_per_solution]     (default 40 per solution = 2000 in all)
Writes wrong_strategies.json, brute_force_timing.json, planted_changes.json and planted_changes_summary.json to OUT_DIR.
"""
import ast
import copy
import importlib.util
import json
import math
import multiprocessing as mp
import pathlib
import random
import signal
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "round3"))
from hidden_bugs import apply_site, sites  # noqa: E402

SPEC_PATH = ROOT / "round1/problems/elevator/spec.py"
CANDIDATES = sorted((ROOT / "round1/candidates/elevator").glob("attempt_*.py"))
PRELUDE = (
    "from typing import *\n"
    "import collections, heapq, bisect, math, itertools, functools, string, re, random\n"
    "from collections import *\nfrom heapq import *\nfrom bisect import *\n"
    "from functools import *\nfrom itertools import *\nfrom math import *\n"
)
MUTANT_SECONDS = 25
SEED = 4023


def load_spec():
    s = importlib.util.spec_from_file_location("elevator_spec", SPEC_PATH)
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m


SPEC = load_spec()


def build_cases():
    """Layer order mirrors what a person does: examples first, then harder."""
    ex = [(a, want) for a, want in SPEC.examples()]
    edge = [(a, SPEC.reference(*a)) for a in SPEC.edge_cases()]
    small = [(a, SPEC.reference(*a)) for a in SPEC.random_cases()]
    medium = [(a, SPEC.fast(*a)) for a in SPEC.medium_cases()]
    return {"examples": ex, "edge": edge, "small": small, "medium": medium}


# ---- A. gut strategies
def gut_nearest(n, start, reqs):
    return SPEC.nearest_first(n, start, reqs)


def _sweep(start, reqs, up_first):
    above = sorted(r for r in reqs if r > start)
    below = sorted((r for r in reqs if r < start), reverse=True)
    return SPEC._cost_of_order(start, (above + below) if up_first else (below + above))


def gut_up_first(n, start, reqs):
    return _sweep(start, reqs, True)


def gut_closer_side(n, start, reqs):
    above = [r - start for r in reqs if r > start]
    below = [start - r for r in reqs if r < start]
    if not above or not below:
        return _sweep(start, reqs, bool(above))
    return _sweep(start, reqs, min(above) <= min(below))


def gut_busier_side(n, start, reqs):
    above = sum(r > start for r in reqs)
    below = sum(r < start for r in reqs)
    return _sweep(start, reqs, above >= below)


GUTS = {
    "nearest floor first": gut_nearest,
    "always go up first": gut_up_first,
    "closer side first, then the other": gut_closer_side,
    "busier side first, then the other": gut_busier_side,
}


def experiment_a(cases):
    out = {}
    for name, fn in GUTS.items():
        row = {}
        for layer, items in cases.items():
            bad = [(a, want, fn(*a)) for a, want in items if fn(*a) != want]
            row[layer] = {"cases": len(items), "wrong": len(bad)}
            if bad:
                worst = max(bad, key=lambda b: (b[2] - b[1]) / max(b[1], 1))
                row[layer]["worst_pct_over"] = round(100 * (worst[2] - worst[1]) / max(worst[1], 1), 1)
                if layer in ("small", "edge"):
                    tiny = min(bad, key=lambda b: (len(b[0][2]), b[0][0]))
                    row[layer]["smallest"] = {"args": tiny[0], "right": tiny[1], "got": tiny[2]}
        out[name] = row
    return out


# ---- B. brute force growth
def experiment_b():
    rng = random.Random(SEED)
    rows = []
    for k in range(6, 12):
        reqs = rng.sample(range(1, 1000), k)
        t0 = time.perf_counter()
        SPEC.reference(1000, 0, reqs)
        rows.append({"requests": k, "orders": math.factorial(k), "seconds": round(time.perf_counter() - t0, 4)})
    per_order = rows[-1]["seconds"] / rows[-1]["orders"]
    big = SPEC.scale_cases()[0][1]
    t0 = time.perf_counter()
    SPEC.fast(*big)
    fast_seconds = time.perf_counter() - t0
    universe_seconds = 4.35e17  # about 13.8 billion years
    return {
        "timings": rows,
        "seconds_per_order": per_order,
        "predicted_20_requests_years": math.factorial(20) * per_order / 3.156e7,
        "orders_digits_1500": len(str(math.factorial(1500))),
        "universe_ages_digits": int(math.lgamma(1501) / math.log(10) + math.log10(per_order) - math.log10(universe_seconds)) + 1,
        "smart_method_1500_seconds": round(fast_seconds, 3),
        "table_entries_1500_approx": 2 * (750 + 1) ** 2,
    }


# ---- C. planted changes






class TimeUp(Exception):
    pass


def _alarm(*_):
    raise TimeUp()


CASES = None


def judge(task):
    """Run one mutant through the layers; stop at the first layer that notices."""
    attempt, site, source = task
    tree = ast.parse(source)
    mutated = apply_site(tree, site)
    code = ast.unparse(mutated)
    res = {"attempt": attempt, "kind": site[1], "code": code, "orig": ast.unparse(tree),
           "caught_by": None, "first_wrong": None, "wrong_in_layer": 0, "layer_size": 0}
    if ast.unparse(tree) == code:
        res["caught_by"] = "no-change"
        return res
    ns = {"__name__": "candidate"}
    signal.signal(signal.SIGALRM, _alarm)
    signal.alarm(MUTANT_SECONDS)
    try:
        exec(compile(PRELUDE + code, "m", "exec"), ns)
        sol = ns["Solution"]
        for layer in ("examples", "edge", "small", "medium"):
            items = CASES[layer]
            wrong = []
            for a, want in items:
                try:
                    got = sol().elevatorRequests(*copy.deepcopy(a))
                except TimeUp:
                    raise
                except Exception as e:
                    got = f"crash: {type(e).__name__}"
                if got != want or type(got) is not int:
                    wrong.append((a, want, got))
            if wrong:
                tiny = min(wrong, key=lambda w: (len(w[0][2]), w[0][0]))
                res.update(caught_by=layer, first_wrong={"args": tiny[0], "right": tiny[1], "got": tiny[2]},
                           wrong_in_layer=len(wrong), layer_size=len(items))
                return res
        for name, a in SPEC.scale_cases():
            t0 = time.perf_counter()
            got = sol().elevatorRequests(*copy.deepcopy(a))
            if got != SPEC.fast(*a) or time.perf_counter() - t0 > 2:
                res.update(caught_by="full-size", first_wrong={"case": name})
                return res
        res["caught_by"] = "survived"
    except TimeUp:
        res["caught_by"] = "hung"
    except Exception as e:
        res["caught_by"] = "crash-on-load"
        res["first_wrong"] = str(e)[:100]
    finally:
        signal.alarm(0)
    return res


def experiment_c(per_attempt, cases):
    global CASES
    CASES = cases
    rng = random.Random(SEED)
    tasks = []
    for path in CANDIDATES:
        source = path.read_text()
        all_sites = sites(ast.parse(source))
        rng.shuffle(all_sites)
        tasks += [(path.stem, s, source) for s in all_sites[:per_attempt]]
    with mp.get_context("fork").Pool(8) as pool:
        return pool.map(judge, tasks, chunksize=4)


def summarise(results):
    tally = {}
    for r in results:
        tally[r["caught_by"]] = tally.get(r["caught_by"], 0) + 1
    by_kind = {}
    for r in results:
        by_kind.setdefault(r["kind"], {}).setdefault(r["caught_by"], 0)
        by_kind[r["kind"]][r["caught_by"]] += 1
    return {"total": len(results), "tally": tally, "by_kind": by_kind}


def main():
    out = pathlib.Path(sys.argv[1])
    out.mkdir(parents=True, exist_ok=True)
    per_attempt = int(sys.argv[2]) if len(sys.argv) > 2 else 40
    cases = build_cases()
    a = experiment_a(cases)
    (out / "wrong_strategies.json").write_text(json.dumps(a, indent=1))
    print("A", json.dumps({k: {l: v[l]["wrong"] for l in v} for k, v in a.items()}))
    b = experiment_b()
    (out / "brute_force_timing.json").write_text(json.dumps(b, indent=1))
    print("B", json.dumps(b))
    results = experiment_c(per_attempt, cases)
    (out / "planted_changes.json").write_text(json.dumps(results))
    s = summarise(results)
    (out / "planted_changes_summary.json").write_text(json.dumps(s, indent=1))
    print("C", json.dumps(s))


if __name__ == "__main__":
    main()
