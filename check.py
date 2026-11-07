#!/usr/bin/env python3
"""Run the case library: the slow machine is the answer key.

  python3 check.py two-sum                     one case
  python3 check.py --all                       every case
  python3 check.py two-sum --answer mine.py    check your own answer (any file with a solve function)
  python3 check.py --list                      list the cases
  python3 check.py --all --write-table         also rewrite the results table in cases/README.md

For each case: fast.py must agree with slow.py on every generated input, and finish a large input in time with an
answer that an independent check accepts, and each wrong answer in wrong.py must fail on at least one input. The smallest failing input is printed. A pass means no
disagreement on the inputs tried. It does not mean no failing input exists.

Standard library only. --answer runs the file you give it on your machine, so read it first.
"""
import argparse
import copy
import importlib.util
import inspect
import os
import pathlib
import platform
import random
import signal
import sys
import time
import zlib
from concurrent.futures import ProcessPoolExecutor

ROOT = pathlib.Path(__file__).resolve().parent
CASES = ROOT / "cases"
TABLE_FILE = CASES / "README.md"
TABLE_BEGIN = "<!-- results table begins: written by check.py --write-table, do not edit -->"
TABLE_END = "<!-- results table ends -->"
DEFAULT_TRIALS = 3000
DEFAULT_SEED = 1
CALL_LIMIT_S = 2.0
BIG_LIMIT_S = 10.0
FAMILIES = (
    "Arrays and hashing", "Two pointers", "Sliding window", "Binary search", "Stacks", "Heaps", "Intervals",
    "Linked structures", "Trees", "Graphs", "Greedy", "Backtracking", "DP: 1D", "DP: 2D", "DP: intervals",
    "DP: bitmask", "Tries", "Bit tricks",
)
CHECK_LIMIT_S = 120.0
sys.dont_write_bytecode = True
sys.setrecursionlimit(20000)
sys.path.insert(0, str(CASES))
from checking import strict_equal  # noqa: E402


class CallTimeout(BaseException):
    """A BaseException, so that an answer's own `except Exception` cannot swallow it."""


def _on_alarm(signum, frame):
    raise CallTimeout()


def timed_call(fn, args, limit, private_copy=True):
    """Call fn on a private copy of args, under a time limit. Return (ok, value_or_error_text)."""
    private = copy.deepcopy(args) if private_copy else args
    has_timer = hasattr(signal, "setitimer")
    if has_timer:
        signal.signal(signal.SIGALRM, _on_alarm)
        signal.setitimer(signal.ITIMER_REAL, limit)
    try:
        return True, fn(*private)
    except CallTimeout:
        return False, f"no answer within {limit:g} s"
    except Exception as e:
        return False, f"raised {type(e).__name__}: {e}"
    finally:
        if has_timer:
            signal.setitimer(signal.ITIMER_REAL, 0)


def load_module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_answer(path):
    module = load_module(pathlib.Path(path).resolve(), "answer_under_check")
    if hasattr(module, "solve"):
        return module.solve
    if hasattr(module, "Solution"):
        solution = module.Solution()
        methods = [n for n in dir(solution) if not n.startswith("_") and callable(getattr(solution, n))]
        if len(methods) == 1:
            return getattr(solution, methods[0])
    raise SystemExit(f"{path}: needs a function named solve, or a Solution class with one public method")


def equal(args, got, want):
    return strict_equal(got, want)


def judge(same, args, got, want):
    """Apply a case's comparison under a time limit. A comparison that crashes or hangs on an answer rejects it."""
    ok, verdict = timed_call(same, (args, got, want), CALL_LIMIT_S, private_copy=False)
    return ok and verdict is True


def safe_repr(value):
    try:
        return repr(value)
    except Exception as e:
        return f"unprintable answer ({type(e).__name__})"


def generate_inputs(meta, name, trials, seed):
    """Distinct inputs, sizes cycling from 0 up, the same every run for a given seed."""
    rng = random.Random(zlib.crc32(name.encode()) ^ seed)
    seen = {}
    for args in getattr(meta, "edges", list)():
        seen.setdefault(repr(args), args)
    for t in range(trials):
        args = meta.generate(rng, t % (meta.MAX_SIZE + 1))
        seen.setdefault(repr(args), args)
    return list(seen.values())


def describe(fn, args):
    names = list(inspect.signature(fn).parameters)
    if len(names) != len(args):
        return ", ".join(repr(a) for a in args)
    return ", ".join(f"{n}={a!r}" for n, a in zip(names, args))


def score_subject(fn, inputs, answers, same, slow):
    """Count failures against the key. Return (fails, smallest) where smallest is None or a dict of text."""
    fails = 0
    smallest = None
    for args, want in zip(inputs, answers):
        ok, got = timed_call(fn, args, CALL_LIMIT_S)
        if ok and judge(same, args, got, want):
            continue
        fails += 1
        key = len(repr(args))
        if smallest is None or key < smallest["key"]:
            smallest = {"key": key, "input": describe(slow, args), "got": safe_repr(got) if ok else got,
                        "want": repr(want)}
    return fails, smallest


def run_case(case_dir, trials=DEFAULT_TRIALS, seed=DEFAULT_SEED, answer_path=None):
    """Run one case and return a plain dict, safe to send between processes."""
    case_dir = pathlib.Path(case_dir).resolve()
    if str(case_dir.parent) not in sys.path:
        sys.path.insert(0, str(case_dir.parent))  # for the shared structures module
    name = case_dir.name
    tag = name.replace("-", "_")
    meta = load_module(case_dir / "cases.py", f"{tag}_cases")
    slow = load_module(case_dir / "slow.py", f"{tag}_slow").solve
    same = getattr(meta, "same", equal)
    inputs = generate_inputs(meta, name, trials, seed)
    answers = []
    for args in inputs:
        ok, want = timed_call(slow, args, CALL_LIMIT_S * 5)
        if not ok:
            return {"name": name, "family": meta.FAMILY, "ok": False, "problems": [
                f"slow.py failed on {describe(slow, args)}: {want}"], "inputs": len(inputs), "subjects": {}}
        answers.append(want)

    result = {"name": name, "family": meta.FAMILY, "title": meta.TITLE, "inputs": len(inputs), "problems": [],
              "subjects": {}}
    if answer_path:
        main_fn, label = load_answer(answer_path), "answer"
    else:
        main_fn, label = load_module(case_dir / "fast.py", f"{tag}_fast").solve, "fast"
    fails, smallest = score_subject(main_fn, inputs, answers, same, slow)
    result["subjects"][label] = {"fails": fails, "smallest": smallest}
    if fails:
        result["problems"].append(f"{label} disagrees with slow on {fails} of {len(inputs)} inputs")

    big_args = meta.big(random.Random(seed))
    begun = time.perf_counter()
    ok, detail = timed_call(main_fn, big_args, BIG_LIMIT_S, private_copy=False)
    result["big_seconds"] = round(time.perf_counter() - begun, 3)
    result["big_checked"] = hasattr(meta, "big_check")
    if not ok:
        result["problems"].append(f"{label} on the large input: {detail}")
    elif result["big_checked"]:
        # A fresh copy, because the answer may have changed its input. A malformed answer makes the check fail or raise.
        fresh = meta.big(random.Random(seed))
        checked, verdict = timed_call(meta.big_check, (fresh, detail), CHECK_LIMIT_S, private_copy=False)
        if not (checked and verdict is True):
            shown = safe_repr(detail)
            shown = shown if len(shown) <= 80 else shown[:77] + "..."
            result["problems"].append(f"{label} on the large input: wrong answer, got {shown}")

    if not answer_path:
        wrong = load_module(case_dir / "wrong.py", f"{tag}_wrong")
        for label in ("gut", "planted"):
            fails, smallest = score_subject(getattr(wrong, label), inputs, answers, same, slow)
            result["subjects"][label] = {"fails": fails, "smallest": smallest}
            if not fails:
                result["problems"].append(f"{label} survived all {len(inputs)} inputs, so it is not shown wrong")
    result["ok"] = not result["problems"]
    return result


def case_dirs():
    return sorted(p for p in CASES.iterdir() if (p / "cases.py").is_file())


def case_family_rank(result):
    family = result["family"]
    return (FAMILIES.index(family) if family in FAMILIES else len(FAMILIES), result["name"])


def print_result(r):
    print(f"{r['name']}  [{r.get('title', '')}]  {r['inputs']} distinct inputs")
    for label, s in r["subjects"].items():
        if s["fails"]:
            m = s["smallest"]
            print(f"  {label:<8} fails {s['fails']} of {r['inputs']}")
            print(f"           smallest input: {m['input']}")
            print(f"           got {m['got']}, slow says {m['want']}")
        else:
            print(f"  {label:<8} agrees with slow on all {r['inputs']}")
    if "big_seconds" in r:
        checked = ", answer checked" if r.get("big_checked") else ", answer not checked"
        print(f"  large input: {r['big_seconds']} s (limit {BIG_LIMIT_S:g} s){checked}")
    for problem in r["problems"]:
        print(f"  PROBLEM: {problem}")
    print(f"  {'OK' if r['ok'] else 'FAILED'}")


def one_line(r):
    subjects = r["subjects"]
    parts = [f"{label} fails {subjects[label]['fails']}" for label in ("gut", "planted") if label in subjects]
    return f"{'OK    ' if r['ok'] else 'FAILED'} {r['name']:<48} {r['inputs']:>5} inputs, fast agrees, " + ", ".join(parts)


def code_cell(text, limit=60):
    text = text if len(text) <= limit else text[:limit - 3] + "..."
    return "`" + text.replace("|", "\\|") + "`"


def table_rows(results):
    rows = ["| Case | Family | Inputs | Fast vs slow | Gut fails | Gut's smallest failing input | Planted fails | "
            "Planted's smallest failing input |", "|---|---|---:|---|---:|---|---:|---|"]
    for r in sorted(results, key=case_family_rank):
        gut, planted = r["subjects"]["gut"], r["subjects"]["planted"]
        agree = "agree" if not r["subjects"]["fast"]["fails"] else "DISAGREE"
        rows.append(f"| [{r['name']}]({r['name']}/) | {r['family']} | {r['inputs']} | {agree} | {gut['fails']} | "
                    f"{code_cell(gut['smallest']['input']) if gut['smallest'] else '-'} | {planted['fails']} | "
                    f"{code_cell(planted['smallest']['input']) if planted['smallest'] else '-'} |")
    return rows


def write_table(results, trials, seed, path=TABLE_FILE):
    version = ".".join(platform.python_version_tuple()[:2])
    block = [TABLE_BEGIN, f"Written by `check.py --all --write-table` with Python {version}, {trials} draws per case, "
             f"seed {seed}. Inputs counts distinct inputs after duplicates are removed.", ""]
    block += table_rows(results) + [TABLE_END]
    text = path.read_text()
    start, end = text.index(TABLE_BEGIN), text.index(TABLE_END) + len(TABLE_END)
    path.write_text(text[:start] + "\n".join(block) + text[end:])


def run_all(trials, seed):
    dirs = case_dirs()
    with ProcessPoolExecutor(max_workers=os.cpu_count() or 2) as pool:
        return list(pool.map(run_case, dirs, [trials] * len(dirs), [seed] * len(dirs)))


def main(argv=None):
    ap = argparse.ArgumentParser(description="Check fast against slow, and show that each wrong answer fails.")
    ap.add_argument("case", nargs="?", help="case folder name under cases/")
    ap.add_argument("--all", action="store_true", help="run every case")
    ap.add_argument("--list", action="store_true", help="list the cases")
    ap.add_argument("--answer", help="check this file instead of fast.py (it runs on your machine: read it first)")
    ap.add_argument("--trials", type=int, default=DEFAULT_TRIALS, help="inputs drawn per case, before removing duplicates")
    ap.add_argument("--seed", type=int, default=DEFAULT_SEED)
    ap.add_argument("--write-table", action="store_true", help="with --all, rewrite the table in cases/README.md")
    a = ap.parse_args(argv)

    if a.list:
        for d in case_dirs():
            print(d.name)
        return 0
    if a.all:
        begun = time.perf_counter()
        results = sorted(run_all(a.trials, a.seed), key=case_family_rank)
        for r in results:
            print(one_line(r))
            for problem in r["problems"]:
                print(f"       PROBLEM: {problem}")
        good = sum(r["ok"] for r in results)
        wrong = sum(1 for r in results for k in ("gut", "planted") if r["subjects"].get(k, {}).get("fails"))
        print(f"\n{good} of {len(results)} cases OK. {wrong} wrong answers each failed on at least one input. "
              f"{time.perf_counter() - begun:.0f} s.")
        if a.write_table:
            write_table(results, a.trials, a.seed)
            print(f"Wrote the table in {TABLE_FILE.relative_to(ROOT)}.")
        return 0 if good == len(results) else 1
    if not a.case:
        ap.error("name a case, or use --all or --list")
    case_dir = CASES / a.case
    if not (case_dir / "cases.py").is_file():
        print(f"no case named {a.case}; try --list", file=sys.stderr)
        return 2
    r = run_case(case_dir, a.trials, a.seed, a.answer)
    print_result(r)
    return 0 if r["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
