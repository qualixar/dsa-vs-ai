"""The one calibration procedure for round three's limits. Run as a script; it writes CALIBRATION-ROUND3.json.

  For each measure:  limit = (1.3 x the reference's worst over 1000 sampled days), raised if needed to the
                     witness's worst on the hand-built days, then rounded up to the next ten.

Sampled days: scenarios_v3.scenario(family, seed) for seed in CALIBRATION_SEEDS. Day events don't depend on the
limits, so the procedure is a fixed point: --check recomputes it and fails if the table in scenarios_v3.py differs.
"""
import argparse
import hashlib
import json
import math
import multiprocessing
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import baselines  # noqa: E402
import envelope_probes  # noqa: E402
import scenarios_v3 as G  # noqa: E402
import sim  # noqa: E402

CALIBRATION_SEEDS = range(500000, 501000)
MULTIPLIER = 1.3
OUT = os.path.join(HERE, "CALIBRATION-ROUND3.json")
HASHED = ("scenarios_v3.py", "sim.py", "baselines.py", "witness.py", "envelope_probes.py", "calibrate_round3.py")
FAMILIES = ("v1", "v2", "v3", "v4", "v5")


def sha(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def ceil10(value):
    return int(math.ceil(value / 10.0 - 1e-9) * 10)


def _measure(task):
    family, seed = task
    sc = {**G.scenario(family, seed), "bound": None, "lobby_p95_target": None, "rush_upper_limit": None}
    r = sim.Simulation(baselines.Baseline, sc).run()
    broken = sum(r["violations"].values())
    return family, seed, r["max_time"], r["lobby_p95"], r["rush_upper_max"], broken


def measure_reference(workers=6):
    tasks = [(f, s) for f in FAMILIES for s in CALIBRATION_SEEDS]
    with multiprocessing.get_context("spawn").Pool(workers) as pool:
        rows = pool.map(_measure, tasks, chunksize=40)
    out = {}
    for family in FAMILIES:
        mine = [r for r in rows if r[0] == family]
        top = max(mine, key=lambda r: r[2])
        out[family] = {"worst_passenger": top[2], "worst_seed": top[1], "rules_broken": sum(r[5] for r in mine),
                       "lobby_p95": max(r[3] or 0 for r in mine), "upstairs": max(r[4] or 0 for r in mine)}
    return out


def table(reference, probes):
    """The arithmetic, on its own so a test can check it by hand."""
    limits = {"everyone": {}, "lobby_p95": None, "upper": None}
    for family in FAMILIES:
        limits["everyone"][family] = ceil10(max(MULTIPLIER * reference[family]["worst_passenger"], probes[family]["everyone"][0]))
    limits["lobby_p95"] = ceil10(max(MULTIPLIER * reference["v5"]["lobby_p95"], probes["v5"]["lobby_p95"][0]))
    limits["upper"] = ceil10(max(MULTIPLIER * reference["v5"]["upstairs"], probes["v5"]["upper"][0]))
    return limits


def calibrate():
    reference = measure_reference()
    probes = {f: envelope_probes.worst(f) for f in FAMILIES}
    return {"rule": "ceil10(max(1.3 x reference worst over the sampled days, witness worst on the hand-built days))",
            "multiplier": MULTIPLIER, "rounding": "up to the next ten",
            "sampled_seeds": [CALIBRATION_SEEDS[0], CALIBRATION_SEEDS[-1]], "sampled_days_per_family": len(CALIBRATION_SEEDS),
            "file_sha256": {name: sha(os.path.join(HERE, name)) for name in HASHED},
            "reference_on_sampled_days": reference, "witness_on_hand_built_days": probes,
            "limits": table(reference, probes)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="fail if the limits in scenarios_v3.py aren't what this computes")
    args = ap.parse_args()
    data = calibrate()
    if data["limits"] != G.current_limits():
        print("MISMATCH\n computed", data["limits"], "\n in file ", G.current_limits())
        return 1
    if not args.check:
        with open(OUT, "w") as f:
            json.dump(data, f, indent=1)
    print(json.dumps(data["limits"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
