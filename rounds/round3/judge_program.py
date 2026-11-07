"""Judge one finished program on the certified days, one version at a time.

  python3 -I judge_program.py PROGRAM_DIR [--versions v1 v2 v3 v4 v5] [--workers 6]

PROGRAM_DIR holds `dispatcher/` and, if the program has one, `modes/`: exactly what a team ships. Nothing else in the
folder is read (tests, notes and plans are not copied to the judge). The days are the 50 per version listed in
results/REFEREE-CERTIFICATE.json. A version passes only if every one of its days breaks no rule and every
passenger arrives within that version's limit. Prints one line per version and the first failing day and rule.
"""
import argparse
import os
import shutil
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import judge as J  # noqa: E402
import scenarios_v3 as G  # noqa: E402

CERTIFICATE = os.path.join(HERE, "results", "REFEREE-CERTIFICATE.json")
FAMILIES = ("v1", "v2", "v3", "v4", "v5")


def clean_days(result, days):
    return sum(not J._bad(result["scenarios"].get(sc["name"], {"violations": {"C1": 1}})) for sc in days)


def judge_program(program, versions, workers, certificate=CERTIFICATE):
    days, batches = G.certified_set(certificate)
    work = os.path.realpath(tempfile.mkdtemp(prefix="program-"))
    try:
        for part in ("dispatcher", "modes"):
            if os.path.isdir(os.path.join(program, part)):
                shutil.copytree(os.path.join(program, part), os.path.join(work, part), ignore=shutil.ignore_patterns("__pycache__"))
        chosen = [sc for family in versions for sc in days[family]]
        result = J.judge_days(work, chosen, batches if "v1" in versions else (), workers=workers)
    finally:
        shutil.rmtree(work, ignore_errors=True)
    rows = {}
    for family in versions:
        ok, first = J.pass_family(result, family, days[family], batches if family == "v1" else ())
        rows[family] = {"passed": ok, "days_clean": clean_days(result, days[family]), "days": len(days[family]), "first_failure": first}
    return rows


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("program")
    ap.add_argument("--versions", nargs="+", choices=FAMILIES, default=list(FAMILIES))
    ap.add_argument("--workers", type=int, default=6)
    args = ap.parse_args(argv)
    if not os.path.isdir(os.path.join(args.program, "dispatcher")):
        raise SystemExit(f"{args.program} has no dispatcher/ folder")
    rows = judge_program(os.path.abspath(args.program), tuple(args.versions), args.workers)
    for family, r in rows.items():
        line = f"version {family[1:]}   {r['days_clean']:>2} of {r['days']} days clean   {'PASS' if r['passed'] else 'FAIL'}"
        if r["first_failure"]:
            line += f"   first failure: day {r['first_failure']['day']}, rule {r['first_failure']['rule']}"
        print(line)
    passed = sum(r["passed"] for r in rows.values())
    print(f"{passed} of {len(rows)} versions pass")
    return 0 if passed == len(rows) else 1


if __name__ == "__main__":
    sys.exit(main())
