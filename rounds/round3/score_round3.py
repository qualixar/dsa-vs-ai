"""Round three's result: four-run case study. Judges the final commit of each team's git working folder, and every commit where its manager said a version was done, on the certified days.

  python3 -I act3/score_round3.py --alone a1/final.json a2/final.json --notes b1/final.json b2/final.json
  python3 -I act3/score_round3.py --practice REPO --practice-limits old

The rule is in the README, under round 3.
"""
import argparse
import json
import os
import shutil
import statistics
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
import baselines  # noqa: E402
import judge as J  # noqa: E402
import referee_certify as RC  # noqa: E402
import scenarios  # noqa: E402
import scenarios_v3 as G  # noqa: E402
import sim  # noqa: E402

FAMILIES = ("v1", "v2", "v3", "v4", "v5")
OUT = os.path.join(ROOT, "runs", "round3", "RESULT.json")
UNEVEN_RATIO = 1.25


def decide(versions_alone, versions_notes):
    """The rule, from each arm's versions passed per valid run. Clean means all five."""
    if len(versions_alone) != 2 or len(versions_notes) != 2:
        return {"winner": "inconclusive", "final_score": {"AI": 2, "DSA": 0}, "clean": {}, "versions_passed": {},
                "versions_total": {}, "sentence": "A run was void twice, so this four-run case study is inconclusive and nobody takes the round."}
    a, b = sum(v == 5 for v in versions_alone), sum(v == 5 for v in versions_notes)
    total_a, total_b = sum(versions_alone), sum(versions_notes)
    counts = {"clean": {"alone": a, "notes": b}, "versions_passed": {"alone": list(versions_alone), "notes": list(versions_notes)},
              "versions_total": {"alone": total_a, "notes": total_b}}
    said = (f"In this four-run case study, the team on its own shipped clean {a} of 2 times and passed {total_a} of 10 versions; "
            f"the team with the architect's notes shipped clean {b} of 2 times and passed {total_b} of 10 versions.")
    if a == 2:
        return {"winner": "AI", "final_score": {"AI": 3, "DSA": 0}, **counts, "sentence": f"{said} AI takes the round: it did the whole job alone, both times."}
    if b > a and total_b > total_a:
        return {"winner": "DSA", "final_score": {"AI": 2, "DSA": 1}, **counts, "sentence": f"{said} DSA takes the round under the rule fixed beforehand. Four runs can't say why."}
    return {"winner": "nobody", "final_score": {"AI": 2, "DSA": 0}, **counts, "sentence": f"{said} Nobody takes the round under the rule fixed beforehand."}


def export(room, commit, folder):
    """Only dispatcher/ and modes/ at this commit, blob by blob: no filters and no attributes from the team's tree."""
    git = ["git", "-c", "core.hooksPath=/dev/null", "-c", "core.fsmonitor=false", "-C", room]
    listing = subprocess.run([*git, "ls-tree", "-r", "-z", commit], capture_output=True, check=True).stdout.decode()
    for row in filter(None, listing.split("\0")):
        meta, name = row.split("\t", 1)
        mode, _, blob = meta.split()
        if not name.startswith(("dispatcher/", "modes/")):
            continue
        data = subprocess.run([*git, "cat-file", "blob", blob], capture_output=True, check=True).stdout
        target = os.path.join(folder, name)
        os.makedirs(os.path.dirname(target), exist_ok=True)
        if mode == "120000":
            os.symlink(data.decode(), target)
        else:
            with open(target, "wb") as f:
                f.write(data)


def judge_commit(room, commit, days, batches, families, workers):
    work = tempfile.mkdtemp(prefix="act3-score-")
    try:
        export(room, commit, work)
        chosen = [sc for f in families for sc in days[f]]
        result = J.judge_days(work, chosen, batches if "v1" in families else (), workers=workers)
    finally:
        shutil.rmtree(work, ignore_errors=True)
    outcome = {f: J.pass_family(result, f, days[f], batches) for f in families}
    return result, outcome


def _clean_days(result, days):
    return sum(not J._bad(result["scenarios"].get(sc["name"], {"violations": {"C1": 1}})) for sc in days)


def quality(result, days):
    """Reported beside the result, never scored."""
    out = {}
    for fam, entries in days.items():
        reports = [result["scenarios"][sc["name"]] for sc in entries if sc["name"] in result["scenarios"]]
        means = [r["mean_time"] for r in reports if r.get("mean_time") is not None]
        out[fam] = {"days_clean": _clean_days(result, entries), "days": len(entries),
                    "mean_passenger_time": round(statistics.mean(means), 1) if means else None,
                    "worst_passenger": max((r.get("max_time") or 0 for r in reports), default=None)}
    rush = [result["scenarios"][sc["name"]] for sc in days.get("v5", []) if sc["name"] in result["scenarios"]]
    out["rush"] = {"lobby_p95_worst": max((r.get("lobby_p95") or 0 for r in rush), default=None),
                   "upstairs_worst": max((r.get("rush_upper_max") or 0 for r in rush), default=None)}
    out["riders_aboard_pct_above_optimum"] = (result.get("q1") or {}).get("pct_above_optimum")
    return out


def assumptions(room, commit):
    p = subprocess.run(["git", "-c", "core.hooksPath=/dev/null", "-C", room, "show", f"{commit}:STATUS.md"], capture_output=True, text=True, errors="replace")
    text = p.stdout if p.returncode == 0 else ""
    index = text.find("Assumptions")
    return text[index:][:4000] if index >= 0 else ""


def clock(final, logs):
    rows = []
    path = os.path.join(logs, "log.jsonl")
    if os.path.isfile(path):
        with open(path) as f:
            rows = [json.loads(line) for line in f]
    seconds = [r["seconds_exact"] for r in rows if "seconds_exact" in r]
    return {"working_minutes": final.get("working_minutes"), "sessions": final.get("sessions"),
            "usage_pauses": sum(str(r.get("subtype", "")).startswith("paused") for r in rows),
            "median_session_s": round(statistics.median(seconds), 1) if seconds else None,
            "longest_session_s": round(max(seconds), 1) if seconds else None}


def score_run(final_path, days, batches, workers):
    with open(final_path) as f:
        final = json.load(f)
    logs = os.path.dirname(final_path)
    valid = bool(final.get("scored")) and str(final.get("outcome", "")).startswith(("finished", "deadline"))
    row = {"run": final.get("run"), "arm": final.get("arm"), "outcome": final.get("outcome"), "valid": valid,
           "setup_hash": final.get("setup_hash"), "clock": clock(final, logs), "final_commit": final.get("final_commit")}
    if not valid:
        return row
    room = final["room"]
    J.DENY_READ[:] = sorted(set(J.DENY_READ) | set(final.get("deny_read", [])))  # judged code can't read any room
    result, outcome = judge_commit(room, final["final_commit"], days, batches, FAMILIES, workers)
    row["passed"] = {f: outcome[f][0] for f in FAMILIES}
    row["first_failure"] = {f: outcome[f][1] for f in FAMILIES if not outcome[f][0]}
    row["versions_passed"] = sum(row["passed"].values())
    row["clean"] = row["versions_passed"] == 5
    row["adjudicated"] = result["adjudicated"]
    row["quality"] = quality(result, days)
    row["assumptions"] = assumptions(room, final["final_commit"])
    row["honesty"] = {}
    for version, commit in final.get("done_commits", {}).items():
        scope = FAMILIES[:FAMILIES.index(version) + 1]
        _, done = judge_commit(room, commit, days, batches, scope, workers)
        row["honesty"][version] = {"commit": commit, "referee_agrees": all(done[f][0] for f in scope),
                                   "first_failure": next((done[f][1] for f in scope if not done[f][0]), None)}
    return row


def uneven(runs):
    """A note for the report, never a score: did the rooms get much the same time?"""
    minutes = [r["clock"]["working_minutes"] for r in runs if r["clock"].get("working_minutes")]
    medians = [r["clock"]["median_session_s"] for r in runs if r["clock"].get("median_session_s")]
    notes = []
    if minutes and min(minutes) > 0 and max(minutes) / min(minutes) > UNEVEN_RATIO:
        notes.append(f"working minutes differ from {min(minutes):.0f} to {max(minutes):.0f}")
    if medians and min(medians) > 0 and max(medians) / min(medians) > UNEVEN_RATIO:
        notes.append(f"median session time differs from {min(medians):.0f} s to {max(medians):.0f} s")
    if any(r["clock"].get("usage_pauses") for r in runs):
        notes.append("usage pauses: " + ", ".join(f"{r['run']} {r['clock']['usage_pauses']}" for r in runs))
    return notes


def board(runs, decision):
    lines = ["| | Run 1 | Run 2 |", "|---|---|---|"]
    for arm, label in (("alone", "AI team on its own"), ("notes", "AI team plus the architect's notes")):
        cells = [f"{r['versions_passed']} of 5" if r.get("valid") else "void" for r in runs if r["arm"] == arm]
        lines.append(f"| {label} | {' | '.join(cells)} |")
    lines += ["", decision["sentence"], ""]
    for r in runs:
        for fam, why in (r.get("first_failure") or {}).items():
            lines.append(f"{r['run']} {fam}: first failure on {why['day']}, rule {why['rule']}")
    return "\n".join(lines)


def score(alone, notes, certificate, out, workers):
    days, batches = G.certified_set(certificate)
    days = {f: days[f] for f in FAMILIES}
    runs = {}
    for path in (*alone, *notes):
        row = score_run(path, days, batches, workers)
        runs[row["run"]] = row
    ordered = list(runs.values())
    for_arm = lambda arm: [r["versions_passed"] for r in ordered if r["arm"] == arm and r["valid"]]  # noqa: E731
    decision = decide(for_arm("alone"), for_arm("notes"))
    with RC.Room(RC.reference_source()) as room:
        reference = quality(J.judge_days(room, [sc for f in FAMILIES for sc in days[f]], batches, workers=workers), days)
    report = {"decision": decision, "runs": runs, "reference_quality": reference, "unevenness": uneven(ordered),
              "setup_hash_matches": len({r["setup_hash"] for r in ordered}) == 1}
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    with open(out, "w") as f:
        json.dump(report, f, indent=1)
    print(board(ordered, decision))
    if report["unevenness"]:
        print("Unevenness to note: " + "; ".join(report["unevenness"]))
    return 0


# ---- the practice run's re-examination: reported either way, never a verdict -------------------------------------
OLD_RUSH_P95 = scenarios.P95_TARGET["v5"]


def _old_day(family, seed):
    day = G.scenario(family, seed, {"everyone": dict(scenarios.BOUNDS), "lobby_p95": None, "upper": None})
    return {**day, "p95_target": OLD_RUSH_P95 if family == "v5" else None}


def _reference_clears(day):
    r = sim.Simulation(baselines.Baseline, day).run()
    within = (r["max_time"] or 0) <= day["bound"] / RC.MARGIN and (day.get("p95_target") is None or (r["p95_time"] or 0) <= day["p95_target"] / RC.MARGIN)
    return within and not any(r["violations"].values())


def practice(repo, certificate, out, workers):
    with open(certificate) as f:
        cert = json.load(f)
    table = {}
    for family in FAMILIES:
        seeds = cert["families"][family]["kept_seeds"]
        days = [_old_day(family, s) for s in seeds]
        kept = [d for d in days if _reference_clears(d)]
        result = J.judge_days(repo, kept, G.q1_batches() if family == "v1" else (), workers=workers)
        rules = {}
        for rule in ("C1", "S1", "S2", "S3", "L1", "T5"):
            rules[rule] = sum(not result["scenarios"].get(d["name"], {"violations": {rule: 1}})["violations"].get(rule) for d in kept)
        table[family] = {"generated": len(days), "excluded_reference_fails_old_limit": len(days) - len(kept), "evaluated": len(kept),
                         "days_passing_per_rule": rules, "first_failure": J.pass_family(result, family, kept, G.q1_batches() if family == "v1" else ())[1]}
    days_new, batches = G.certified_set(certificate)
    new = J.judge_days(repo, [sc for f in FAMILIES for sc in days_new[f]], batches, workers=workers)
    info = {f: {"passes_round_three_limits": J.pass_family(new, f, days_new[f], batches)[0], "first_failure": J.pass_family(new, f, days_new[f], batches)[1]} for f in FAMILIES}
    report = {"status": "unscored: this code ran under a different brief, with the roadmap in view and no deadline",
              "old_brief_limits": table, "information_only_round_three_limits": info}
    with open(out, "w") as f:
        json.dump(report, f, indent=1)
    print(json.dumps(table, indent=1))
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--alone", nargs=2, default=[])
    ap.add_argument("--notes", nargs=2, default=[])
    ap.add_argument("--practice")
    ap.add_argument("--practice-limits", choices=["old"], default="old")
    ap.add_argument("--certificate", default=G.CERTIFICATE)
    ap.add_argument("--out", default=None)
    ap.add_argument("--workers", type=int, default=6)
    args = ap.parse_args(argv)
    if args.practice:
        return practice(args.practice, args.certificate, args.out or os.path.join(ROOT, "runs", "round3", "PRACTICE.json"), args.workers)
    return score(args.alone, args.notes, args.certificate, args.out or OUT, args.workers)


if __name__ == "__main__":
    sys.exit(main())
