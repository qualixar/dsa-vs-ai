"""Grades AI-written solutions through four gates.

  Gate 0  examples      LeetCode's own examples ("looks done")
  Gate 1  correctness   edge cases + 3,000 random small cases vs the slow reference,
                        + 600 medium cases vs the fast solution (itself checked
                        against the reference in the self-tests)
  Gate 2  scale         the problem's real limits, 2 s per case (timed by the grader,
                        not by the candidate), 2 GB memory
  Gate 3  sanity        rules no correct answer can break, on every output

Usage:
  python3 -I grade.py rain     candidates/rain/*.py     --out results/rain.json
  python3 -I grade.py elevator candidates/elevator/*.py --out results/elevator.json

Threat model: candidates are cooperative but may be buggy. Each batch runs in
its own temporary folder inside macOS sandbox-exec: no network, no writes outside
that folder, no reads of this harness (so no expected answers) or of the home folder. Results travel
over a private pipe, so candidate prints can't corrupt them. Every candidate is
also scanned for calls that could interfere (exit, os.write, time patching...);
any hits are listed in the results for readers to inspect.
"""
import argparse
import hashlib
import importlib.util
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import threading
import time

HERE = os.path.dirname(os.path.abspath(__file__))
SCALE_LIMIT_S = 2.0  # our fast references take <= 0.15 s; O(n^2) rain takes ~3 s
GATE_TIMEOUT_S = {"examples": 20, "correctness": 120}
MEMORY_LIMIT_MB = 2048
MAX_PROTOCOL_BYTES = 50_000_000
HOME = os.path.expanduser("~")
FLAG_PATTERNS = r"os\.write|os\._exit|sys\.exit|\bexit\(|\bquit\(|\bopen\(|subprocess|socket|urllib|ctypes|signal|importlib|__import__|builtins|perf_counter|time\.time|multiprocessing|setrecursionlimit|sys\.stdout"


class HarnessError(RuntimeError):
    """The grader itself failed; the run must be repeated, not scored."""


def sandbox_profile(workdir):
    """No network; writes only in the batch folder; no reads of this harness or
    of the user's home folder (except Python itself, if it is installed there)."""
    rules = ["(version 1)", "(allow default)", "(deny network*)", "(deny file-write*)",
             f'(allow file-write* (subpath "{workdir}") (subpath "/dev"))']
    for p in (HERE, HOME):
        rules.append(f'(deny file-read* (subpath "{os.path.realpath(p)}"))')
    for p in {sys.prefix, sys.base_prefix, os.path.dirname(sys.executable)}:
        rp = os.path.realpath(p)
        if rp.startswith(os.path.realpath(HOME)):
            rules.append(f'(allow file-read* (subpath "{rp}"))')
    rules.append(f'(allow file-read* (subpath "{workdir}"))')
    return "".join(rules)


def load_spec(problem):
    path = os.path.join(HERE, "problems", problem, "spec.py")
    s = importlib.util.spec_from_file_location(f"spec_{problem}", path)
    mod = importlib.util.module_from_spec(s)
    s.loader.exec_module(mod)
    return mod


def group_rss_mb(pgid):
    """Memory of every process in the candidate's process group, in MB."""
    try:
        pids = subprocess.run(["pgrep", "-g", str(pgid)], capture_output=True,
                              text=True, timeout=2).stdout.split()
        if not pids:
            return 0.0
        out = subprocess.run(["ps", "-o", "rss=", "-p", ",".join(pids)],
                             capture_output=True, text=True, timeout=2).stdout
        return sum(int(x) for x in out.split()) / 1024
    except (subprocess.TimeoutExpired, ValueError) as e:
        raise HarnessError(f"memory watchdog failed: {e}")


def run_batch(candidate, method, cases, timeout):
    """Run cases in one sandboxed process.
    Returns (results | None, error | None, wall_seconds measured by the grader)."""
    workdir = os.path.realpath(tempfile.mkdtemp(prefix="grade-"))
    try:
        shutil.copy(os.path.join(HERE, "runner.py"), workdir)
        shutil.copy(candidate, os.path.join(workdir, "candidate.py"))
        with open(os.path.join(workdir, "job.json"), "w") as f:
            json.dump({"candidate": os.path.join(workdir, "candidate.py"),
                       "method": method, "cases": cases}, f)
        r_fd, w_fd = os.pipe()
        cmd = ["sandbox-exec", "-p", sandbox_profile(workdir), sys.executable, "-I", "-B",
               os.path.join(workdir, "runner.py"), os.path.join(workdir, "job.json"), str(w_fd)]
        chunks, size = [], [0]

        def drain():
            with os.fdopen(r_fd, "rb") as r:
                while block := r.read(65536):
                    if size[0] < MAX_PROTOCOL_BYTES:
                        chunks.append(block)
                    size[0] += len(block)

        reader = threading.Thread(target=drain, daemon=True)
        reader.start()
        with open(os.path.join(workdir, "stderr.txt"), "w") as err:
            t0 = time.perf_counter()
            p = subprocess.Popen(cmd, cwd=workdir, stdout=subprocess.DEVNULL, stderr=err,
                                 pass_fds=(w_fd,), start_new_session=True)
            os.close(w_fd)
            killed = None
            while p.poll() is None:
                if time.perf_counter() - t0 > timeout:
                    killed = f"timeout after {timeout}s"
                elif group_rss_mb(p.pid) > MEMORY_LIMIT_MB:
                    killed = f"memory over {MEMORY_LIMIT_MB} MB"
                if killed:
                    try:
                        os.killpg(p.pid, signal.SIGKILL)
                    except ProcessLookupError:
                        pass
                    p.wait()
                    break
                time.sleep(0.02)
            wall = time.perf_counter() - t0
        reader.join(timeout=5)
        if killed:
            return None, killed, wall
        if p.returncode != 0:
            with open(os.path.join(workdir, "stderr.txt")) as f:
                tail = f.read()[-300:]
            return None, f"process exited with code {p.returncode}: {tail}", wall
        if size[0] > MAX_PROTOCOL_BYTES:
            return None, "result too large", wall
        try:
            out = json.loads(b"".join(chunks))
        except json.JSONDecodeError:
            return None, "no valid result from the runner", wall
        if not isinstance(out, dict) or "results" not in out or "load_error" not in out:
            return None, "malformed result", wall
        if out["load_error"]:
            return None, out["load_error"], wall
        res = out["results"]
        if not isinstance(res, list) or len(res) != len(cases) or not all(
                isinstance(r, dict) and {"value", "error", "seconds"} <= r.keys() for r in res):
            return None, f"expected {len(cases)} results, got a malformed or short list", wall
        return res, None, wall
    finally:
        shutil.rmtree(workdir, ignore_errors=True)


def answer_of(r):
    """What the candidate returned, for comparison and display."""
    if r["error"]:
        return r["error"]
    if r.get("type") != "int":
        return f"<{r.get('type')}> {r.get('repr', '')}"
    return r["value"]


def mismatches(cases, expected, results):
    return [{"input": a, "expected": w, "got": answer_of(r)}
            for a, w, r in zip(cases, expected, results)
            if r["error"] or r.get("type") != "int" or r["value"] != w]


def shortest(failures):
    return min(failures, key=lambda f: len(json.dumps(f["input"]))) if failures else None


def sha256_file(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def grade_one(spec, candidate, fingerprint=None):
    with open(candidate) as f:
        source = f.read()
    rec = {"candidate": os.path.basename(candidate), "sha256": sha256_file(candidate),
           "harness_fingerprint": fingerprint, "flags": sorted(set(re.findall(FLAG_PATTERNS, source))),
           "gates": {}, "first_fail": None}
    outputs = []  # (args, value) for the sanity gate

    # Gate 0: examples
    cases = [a for a, _ in spec.examples()]
    want = [w for _, w in spec.examples()]
    res, err, wall = run_batch(candidate, spec.METHOD, cases, GATE_TIMEOUT_S["examples"])
    if err:
        rec["gates"]["examples"] = {"pass": False, "fail": {"error": err}, "seconds": round(wall, 3)}
    else:
        bad = mismatches(cases, want, res)
        rec["gates"]["examples"] = {"pass": not bad, "fail": bad[0] if bad else None,
                                    "seconds": round(wall, 3)}
        outputs += [(a, r["value"]) for a, r in zip(cases, res) if r.get("type") == "int"]

    # Gate 1: small cases vs the slow reference, medium cases vs the checked fast solution
    small = spec.edge_cases() + spec.random_cases()
    medium = spec.medium_cases()
    cases = small + medium
    want = [spec.reference(*a) for a in small] + [spec.fast(*a) for a in medium]
    res, err, wall = run_batch(candidate, spec.METHOD, cases, GATE_TIMEOUT_S["correctness"])
    if err:
        g1 = {"pass": False, "fail": {"error": err}, "mismatches": None, "of": len(cases)}
    else:
        bad = mismatches(cases, want, res)
        g1 = {"pass": not bad, "fail": shortest(bad), "mismatches": len(bad), "of": len(cases)}
        outputs += [(a, r["value"]) for a, r in zip(cases, res) if r.get("type") == "int"]
    g1["seconds"] = round(wall, 3)
    rec["gates"]["correctness"] = g1

    # Gate 2: scale, one process per case, timed by the grader
    scale = []
    for name, args in spec.scale_cases():
        want = spec.fast(*args)
        res, err, wall = run_batch(candidate, spec.METHOD, [args], SCALE_LIMIT_S + 5)
        if err:
            scale.append({"case": name, "pass": False, "why": err, "seconds": round(wall, 3)})
            continue
        r = res[0]
        wrong = r["error"] or r.get("type") != "int" or r["value"] != want
        slow = wall > SCALE_LIMIT_S
        why = (str(answer_of(r))[:200] if r["error"] or r.get("type") != "int"
               else "wrong answer" if wrong else f"too slow ({wall:.2f}s)" if slow else None)
        scale.append({"case": name, "pass": not (wrong or slow), "why": why,
                      "seconds": round(wall, 3), "candidate_reported_s": round(r["seconds"], 3)})
        if r.get("type") == "int":
            outputs.append((args, r["value"]))
    rec["gates"]["scale"] = {"pass": all(s["pass"] for s in scale), "cases": scale}

    # Gate 3: sanity rules on every integer answer the candidate produced
    broken = [{"input_size": len(json.dumps(a)), "why": why}
              for a, v in outputs if (why := spec.sanity(a, v))]
    rec["gates"]["sanity"] = {"pass": (not broken) if outputs else None, "checked": len(outputs),
                              "broken": broken[:5], "broken_count": len(broken)}

    for gate in ("examples", "correctness", "scale", "sanity"):
        if rec["gates"][gate]["pass"] is False:
            rec["first_fail"] = gate
            break
    rec["survived"] = rec["first_fail"] is None
    return rec


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("problem", choices=["rain", "elevator"])
    ap.add_argument("candidates", nargs="+")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    sys.path.insert(0, HERE)
    import freeze
    fp = freeze.fingerprint()
    spec = load_spec(a.problem)
    records = []
    for c in sorted(a.candidates):
        rec = grade_one(spec, c, fp)
        records.append(rec)
        print(f"{rec['candidate']}: {'SURVIVED' if rec['survived'] else 'out at ' + rec['first_fail']}"
              + (f"  flags: {', '.join(rec['flags'])}" if rec["flags"] else ""))
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    json.dump({"problem": a.problem, "harness_fingerprint": fp, "scale_limit_s": SCALE_LIMIT_S,
               "memory_limit_mb": MEMORY_LIMIT_MB, "machine": "Apple M5 Pro",
               "python": sys.version.split()[0], "records": records},
              open(a.out, "w"), indent=1)


if __name__ == "__main__":
    main()
