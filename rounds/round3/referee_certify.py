"""Measures the referee before it judges anyone, and writes the certificate that freezes it.

  python3 -I referee_certify.py --sealed-hash H --salt S --out REFEREE-CERTIFICATE.json

Steps: draw the days from the frozen hash and the salt; keep those a known solution passes with margin; run the five
broken dispatchers and the planted mutants through the sandboxed judge on the kept days; name the climax day. Exits
non-zero and writes nothing if a family keeps too few days, the reference fails, or a broken dispatcher passes.
"""
import argparse
import ast
import hashlib
import json
import multiprocessing
import os
import pathlib
import random
import shutil
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
import baselines  # noqa: E402
import judge as J  # noqa: E402
import scenarios_v3 as G  # noqa: E402
import sim  # noqa: E402

FAMILIES = ("v1", "v2", "v3", "v4", "v5")
MARGIN = 1.15
RANDOM_DAYS, CANDIDATES, HARDEST, MIN_KEEP, FRESH_MUTANTS, EXISTING_BUGS = 40, 200, 10, 45, 20, 20
BROKEN = {"IgnoresFire": "S2", "MovesWhileOutOfService": "S3", "WrongCommandCount": "C1",
          "FallsThroughFloor": "S1", "OnlyCarCalls": "L1"}
BUGS_DIR = os.path.join(ROOT, "runs", "hidden-bugs")
HASHED = ("scenarios_v3.py", "sim.py", "judge.py", "team_host.py", "baselines.py", "witness.py", "envelope_probes.py",
          "calibrate_round3.py", "referee_certify.py", "CALIBRATION-ROUND3.json")


def sha(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def say(text):
    print(text, flush=True)


def reference_source():
    source = pathlib.Path(HERE, "baselines.py").read_text()
    return source.split("class OptimalOnboard")[0].replace("class Baseline:", "class Dispatcher:")


def broken_source(name):
    source = pathlib.Path(HERE, "baselines.py").read_text()
    return f"{source}\nDispatcher = {name}\n"


def _hardness(task):
    family, seed = task
    sc = G.scenario(family, seed)
    r = sim.Simulation(baselines.Baseline, sc).run()
    ratios = [(r["max_time"] or 0) / sc["bound"]]
    if family == "v5":
        ratios += [(r["lobby_p95"] or 0) / sc["lobby_p95_target"], (r["rush_upper_max"] or 0) / sc["rush_upper_limit"]]
    return seed, max(ratios), sum(r["violations"].values()), r["max_time"]


def choose_days(sealed_hash, salt, family, random_days, candidates, hardest, pool):
    """The random days plus the hardest of a further draw; a day counts only if the reference passes it with margin."""
    drawn = G.seeds(family, sealed_hash, salt, random_days + candidates)
    rows = pool.map(_hardness, [(family, s) for s in drawn], chunksize=8)
    with_margin = [r for r in rows if r[2] == 0 and r[1] <= 1 / MARGIN]
    allowed = {r[0] for r in with_margin}
    kept = [s for s in drawn[:random_days] if s in allowed]
    extra = sorted((r for r in with_margin if r[0] in set(drawn[random_days:])), key=lambda r: -r[1])[:hardest]
    kept += [r[0] for r in extra]
    return {"generated": len(drawn), "kept": len(kept), "kept_seeds": kept, "hardest_seeds": [r[0] for r in extra],
            "dropped_on_margin": len(rows) - len(with_margin), "not_chosen": len(with_margin) - len(kept),
            "reference_worst": max((r[3] or 0) for r in rows if r[0] in set(kept)) if kept else None}


class Room:
    """A folder holding one dispatcher source, the way a team's repository holds it."""
    def __init__(self, source):
        self.source, self.dir = source, None

    def __enter__(self):
        self.dir = tempfile.mkdtemp(prefix="act3-cert-")
        pathlib.Path(self.dir, "dispatcher").mkdir()
        pathlib.Path(self.dir, "dispatcher", "__init__.py").write_text(self.source)
        return self.dir

    def __exit__(self, *_):
        shutil.rmtree(self.dir, ignore_errors=True)


def _all_days(days):
    return [sc for fam in FAMILIES if fam in days for sc in days[fam]]


def compare(result, base):
    """What a planted change did, day by day, against the unchanged code."""
    if result.get("import_error"):
        return {"changed_trace": True, "broke_rule": True, "first": {"day": None, "rule": "import"}}
    changed, broke = False, None
    for name, base_report in base["scenarios"].items():
        r = result["scenarios"].get(name, {})
        changed = changed or r.get("trace") != base_report.get("trace")
        new = {k for k, v in r.get("violations", {}).items() if v and not base_report["violations"].get(k)}
        if new and broke is None:
            broke = {"day": name, "rule": sorted(new)[0]}
    changed = changed or result.get("q1_traces") != base.get("q1_traces")
    for name, b in (base.get("q1", {}).get("batches") or {}).items():
        now = (result.get("q1", {}).get("batches") or {}).get(name, {})
        if b["complete"] and not now.get("complete") and broke is None:
            broke = {"day": name, "rule": "riders-aboard"}
    return {"changed_trace": bool(changed), "broke_rule": broke is not None, "first": broke}


def _block(rows):
    changed = sum(r["changed_trace"] for r in rows)
    broke = sum(r["broke_rule"] for r in rows)
    return {"planted": len(rows), "changed_a_trace": changed, "broke_a_rule": broke,
            "only_shifted_quality": sum(r["changed_trace"] and not r["broke_rule"] for r in rows),
            "changed_nothing": sum(not r["changed_trace"] for r in rows),
            "catch_rate": f"{broke} of {changed} planted bugs that change what the lifts do; {broke} of {len(rows)} planted in all",
            "rows": rows}


def run_broken(days, batches, workers):
    rows = {}
    for name, rule in BROKEN.items():
        with Room(broken_source(name)) as room:
            result = J.judge_days(room, _all_days(days), batches, workers=workers)
        seen = {}
        for report in result["scenarios"].values():
            for key, value in report["violations"].items():
                if value:
                    seen[key] = seen.get(key, 0) + 1
        rows[name] = {"expected_rule": rule, "caught": bool(seen.get(rule)), "days_breaking_the_rule": seen.get(rule, 0),
                      "rules_seen": seen, "import_error": result["import_error"]}
        say(f"  {name:24s} must break {rule:3s}: {'CAUGHT' if rows[name]['caught'] else 'MISSED'} on {seen.get(rule, 0)} days")
    return {"planted": len(rows), "caught": sum(r["caught"] for r in rows.values()), "rows": rows}


def plant_mutants(count, sealed_hash, salt):
    """One small change each to the reference, with the existing planting code: (site description, changed source)."""
    if count == 0:
        return []
    sys.path.insert(0, os.path.join(ROOT, "tools"))
    import hidden_bugs  # noqa: E402  (imported here: only certification plants bugs)
    source = reference_source()
    usable = []
    for site in hidden_bugs.sites(ast.parse(source)):
        try:
            changed, line = hidden_bugs.edit_text(source, site)
        except (ValueError, AssertionError):
            continue
        same = ast.dump(ast.parse(changed)) == ast.dump(hidden_bugs.apply_site(ast.parse(source), site))
        if same and changed != source:
            usable.append((site, changed, line))
    chosen = random.Random(f"{sealed_hash}:{salt}:mutants").sample(usable, count)
    lines = source.split("\n")
    return [({"kind": s[1], "line_no": line, "before": lines[line - 1].strip(), "after": c.split("\n")[line - 1].strip()}, c)
            for s, c, line in chosen]


def run_fresh(count, sealed_hash, salt, days, batches, base, workers):
    rows = []
    for i, (where, source) in enumerate(plant_mutants(count, sealed_hash, salt)):
        with Room(source) as room:
            result = J.judge_days(room, _all_days(days), batches, workers=workers)
        rows.append({"bug": i, **where, **compare(result, base)})
        say(f"  fresh mutant {i:2d}: {'caught' if rows[-1]['broke_rule'] else 'changed nothing a rule sees' if not rows[-1]['changed_trace'] else 'shifted quality only'}")
    return _block(rows)


def run_existing(count, days, batches, workers):
    """The bugs planted in an earlier run's v2 code, judged on families v1 and v2: that code's scope."""
    scope = {f: days[f] for f in ("v1", "v2") if f in days}
    if count == 0:
        return _block([])
    base = J.judge_days(os.path.join(BUGS_DIR, "base"), _all_days(scope), batches, workers=workers)
    with open(os.path.join(BUGS_DIR, "bugs.json")) as f:
        where = json.load(f)
    rows = []
    for row in where[:count]:
        repo = os.path.join(BUGS_DIR, "bugs", f"{row['bug']:02d}")
        result = J.judge_days(repo, _all_days(scope), batches, workers=workers)
        rows.append({"bug": row["bug"], "kind": row["kind"], **compare(result, base)})
        say(f"  existing bug {row['bug']:2d}: {'caught' if rows[-1]['broke_rule'] else 'changed nothing a rule sees' if not rows[-1]['changed_trace'] else 'shifted quality only'}")
    block = _block(rows)
    block["unchanged_code_first_failures"] = {f: J.pass_family(base, f, scope[f], batches)[1] for f in scope}
    return block


def climax(days):
    """The first v4 day where a lift is out when the fire starts and comes back during it."""
    for sc in days.get("v4", []):
        fire = next(e for e in sc["events"] if e[0] == "mode" and e[2] == "fire")
        end = next(e for e in sc["events"] if e[0] == "mode" and e[2] == "normal")
        out = set()
        for e in sc["events"]:
            if e[0] == "service" and e[1] <= fire[1]:
                out = out - {e[2]} if e[3] else out | {e[2]}
        if any(e[0] == "service" and e[3] and e[2] in out and fire[1] < e[1] < end[1] for e in sc["events"]):
            return sc["name"]
    return None


def _refuse(why):
    say("REFUSED: " + why)
    return 1


def certify(sealed_hash, salt, out, workers=6, random_days=RANDOM_DAYS, candidates=CANDIDATES, hardest=HARDEST,
            min_keep=MIN_KEEP, fresh_mutants=FRESH_MUTANTS, existing_bugs=EXISTING_BUGS):
    families = {}
    with multiprocessing.get_context("spawn").Pool(workers) as pool:
        for family in FAMILIES:
            families[family] = choose_days(sealed_hash, salt, family, random_days, candidates, hardest, pool)
            e = families[family]
            say(f"{family}: {e['generated']} days generated, {e['kept']} kept, {e['dropped_on_margin']} dropped on margin, reference worst {e['reference_worst']} s")
            if e["kept"] < min_keep:
                return _refuse(f"{family} keeps {e['kept']} days, fewer than {min_keep}: the limits are wrong")
    days = {f: [G.scenario(f, s) for s in families[f]["kept_seeds"]] for f in FAMILIES}
    batches = G.q1_batches()
    with Room(reference_source()) as room:
        base = J.judge_days(room, _all_days(days), batches, workers=workers)
    failed = {f: J.pass_family(base, f, days[f], batches)[1] for f in FAMILIES if not J.pass_family(base, f, days[f], batches)[0]}
    if failed:
        return _refuse(f"the reference fails through the sandbox: {failed}")
    say("reference through the sandbox: every kept day passes")
    say("broken dispatchers:")
    broken = run_broken(days, batches, workers)
    if broken["caught"] != broken["planted"]:
        return _refuse("a broken dispatcher passed: " + str([k for k, r in broken["rows"].items() if not r["caught"]]))
    say("planted bugs:")
    fresh = run_fresh(fresh_mutants, sealed_hash, salt, days, batches, base, workers)
    existing = run_existing(existing_bugs, days, batches, workers)
    say(f"fresh mutants: {fresh['catch_rate']}")
    say(f"earlier run's bugs: {existing['catch_rate']}")
    certificate = {"sealed_hash": sealed_hash, "salt": salt, "limits": G.current_limits(), "margin": MARGIN,
                   "file_sha256": {name: sha(os.path.join(HERE, name)) for name in HASHED},
                   "families": families, "riders_aboard_batches": len(batches),
                   "broken_dispatchers": broken, "mutants": {"fresh": fresh, "existing": existing},
                   "climax_day": climax(days)}
    with open(out, "w") as f:
        json.dump(certificate, f, indent=1)
    say(f"certificate written; climax day {certificate['climax_day']}; sha256 {sha(out)}")
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sealed-hash", required=True)
    ap.add_argument("--salt", required=True)
    ap.add_argument("--out", default=os.path.join(ROOT, "sealed", "REFEREE-CERTIFICATE.json"))
    ap.add_argument("--workers", type=int, default=6)
    args = ap.parse_args()
    if os.path.exists(args.out):
        raise SystemExit(f"{args.out} exists: a certificate is never rewritten")
    return certify(args.sealed_hash, args.salt, args.out, workers=args.workers)


if __name__ == "__main__":
    sys.exit(main())
