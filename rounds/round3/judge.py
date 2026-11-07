"""Runs a team's code through the simulator. The simulator and the scoring stay in this
process; the team's code runs in a separate sandboxed process (no network, writes only in
a temp folder, no reads of this folder or the home folder) that sees only the contract's
calls. It can't read the event scripts or touch the score, whatever it does.

  python3 -I judge.py <repo> --upto v3 --out judged.json
"""
import argparse
import concurrent.futures
import concurrent.futures.process
import hashlib
import json
import multiprocessing
import os
import select
import shutil
import signal
import subprocess
import sys
import tempfile
import threading
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import scenarios  # noqa: E402
import sim  # noqa: E402

SCENARIO_LIMIT_S = 20
TOTAL_LIMIT_S = 240      # old rounds only: judge(). Round three (judge_days) has no total deadline
DAY_CPU_LIMIT_S = 60     # round three: the team process's own CPU per day, enforced by the kernel
DAY_WATCHDOG_S = 180     # round three: wall clock per day, generous; only a guard against a silent hang
STDERR_KEEP_BYTES = 65536
TESTS_LIMIT_S = 300
MAX_REPLY_BYTES = 1_000_000
MAX_OUTPUT_CHARS = 2_000_000
DENY_READ = []  # folders team code must not read, such as other runs' working folders
CLEAN_ENV = {"PATH": "/usr/bin:/bin", "LANG": "en_US.UTF-8", "PYTHONDONTWRITEBYTECODE": "1"}


class TeamError(Exception):
    """The team's method raised or returned nonsense: a contract failure the simulator records."""


class TeamStopped(BaseException):
    """The team's process hung or died; this scenario can't continue."""


class TeamTimedOut(TeamStopped):
    """No reply before the watchdog ran out. On its own this proves nothing: it is adjudicated alone."""


class ImportFailed(BaseException):
    pass


class InfraError(BaseException):
    """Our sandbox or tooling failed, not the team's code. Outside Exception on purpose: the simulator
    records any Exception as the team's contract failure, and this must reach whoever runs the judge."""


def profile(workdir):
    home = os.path.realpath(os.path.expanduser("~"))
    rules = ["(version 1)", "(allow default)", "(deny network*)", "(deny file-write*)",
             f'(allow file-write* (subpath "{workdir}") (subpath "/dev"))',
             f'(deny file-read* (subpath "{home}"))',
             f'(deny file-read* (subpath "{os.path.realpath(HERE)}"))']
    rules += [f'(deny file-read* (subpath "{os.path.realpath(p)}"))' for p in DENY_READ]
    for p in {sys.prefix, sys.base_prefix}:
        if os.path.realpath(p).startswith(home):
            rules.append(f'(allow file-read* (subpath "{os.path.realpath(p)}"))')
    rules.append(f'(allow file-read* (subpath "{workdir}"))')
    return "".join(rules)


class RemoteDispatcher:
    """Looks like a Dispatcher to the simulator; every call goes to the team's process."""
    def __init__(self, work, floors, lifts, limit, cpu_limit=None):
        self.left, self.buf, self.proc, self.cpu_s, self.stderr_tail = limit, b"", None, 0.0, b""
        self.timeout_text = f"watchdog: no reply within {limit} s" if cpu_limit else f"scenario exceeded {SCENARIO_LIMIT_S} s of compute"
        to_child_r, self.to_child = os.pipe()
        self.from_child, from_child_w = os.pipe()
        host = os.path.join(work, "team_host.py")
        cmd = ["sandbox-exec", "-p", profile(work), sys.executable, "-I", host,
               str(to_child_r), str(from_child_w), os.path.join(work, "team")]
        if cpu_limit:  # the kernel counts this process's CPU, so a busy machine can't count against the team
            cmd = ["/bin/sh", "-c", 'ulimit -t "$1"; shift; exec "$@"', "sh", str(int(cpu_limit)), *cmd]
        try:
            self.proc = subprocess.Popen(cmd, cwd=work, env=CLEAN_ENV, pass_fds=(to_child_r, from_child_w),
                                         stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                                         stderr=subprocess.PIPE, start_new_session=True)
        except OSError as e:
            raise InfraError(f"could not start the sandbox: {e}") from None
        os.close(to_child_r)
        os.close(from_child_w)
        self.drainer = threading.Thread(target=self._drain_stderr, daemon=True)
        self.drainer.start()
        hello = self._read()
        if hello is None:
            try:
                code = self.proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                raise ImportFailed("the code closed its pipe while being imported") from None
            self.drainer.join(timeout=2)
            err = self.stderr_tail.decode(errors="replace")
            if code and err.startswith("sandbox-exec:"):
                raise InfraError("sandbox refused to start: " + err[-300:])
            raise ImportFailed("the code exited while being imported")
        if "import_error" in hello:
            raise ImportFailed(hello["import_error"])
        self._rpc("__init__", (floors, lifts))

    def _drain_stderr(self):
        """Read the team's stderr as it comes and keep only the end, so logging can never fill the pipe and stall it."""
        try:
            fd = self.proc.stderr.fileno()
            while True:
                chunk = os.read(fd, 65536)
                if not chunk:
                    return
                self.stderr_tail = (self.stderr_tail + chunk)[-STDERR_KEEP_BYTES:]
        except (OSError, ValueError):
            return

    def _read(self):
        """One reply line, or None if the process ended. Runs out the scenario's compute budget."""
        while b"\n" not in self.buf:
            t0 = time.monotonic()
            ready, _, _ = select.select([self.from_child], [], [], max(self.left, 0))
            self.left -= time.monotonic() - t0
            if not ready:
                raise TeamTimedOut(self.timeout_text)
            chunk = os.read(self.from_child, 65536)
            if not chunk:
                return None
            self.buf += chunk
            if len(self.buf) > MAX_REPLY_BYTES:
                raise TeamStopped("reply too large")
        line, _, self.buf = self.buf.partition(b"\n")
        try:
            reply = json.loads(line)
        except ValueError:
            raise TeamStopped("unreadable reply") from None
        return reply if isinstance(reply, dict) else {"e": "unreadable reply"}

    def _rpc(self, method, args):
        try:
            os.write(self.to_child, (json.dumps({"m": method, "a": list(args)}) + "\n").encode())
        except OSError:
            raise TeamStopped("process ended") from None
        reply = self._read()
        if reply is None:
            raise TeamStopped("process ended")
        if "e" in reply:
            raise TeamError(reply["e"])
        return reply.get("r")

    def on_call(self, *a):
        return self._rpc("on_call", a)

    def on_car_request(self, *a):
        return self._rpc("on_car_request", a)

    def set_mode(self, *a):
        return self._rpc("set_mode", a)

    def set_lift_available(self, *a):
        return self._rpc("set_lift_available", a)

    def step(self, *a):
        return self._rpc("step", a)

    def close(self):
        for fd in (self.to_child, self.from_child):
            try:
                os.close(fd)
            except OSError:
                pass
        if self.proc:
            try:
                os.killpg(self.proc.pid, signal.SIGKILL)
            except OSError:
                pass
            self._reap()
            self.drainer.join(timeout=2)
            self.proc.stderr.close()

    def _reap(self):
        """Wait for the process and take its CPU from the kernel. Already reaped: nothing to measure."""
        try:
            _, status, usage = os.wait4(self.proc.pid, 0)
        except ChildProcessError:
            self.proc.wait()
            return
        self.proc.returncode = os.waitstatus_to_exitcode(status)
        self.cpu_s = usage.ru_utime + usage.ru_stime


def stopped_report(sc, why):
    return {"scenario": sc["name"], "stopped": why,
            "violations": {"C1": 1, "S1": 0, "S2": 0, "S3": 0, "L1": 0, "T5": 0},
            "examples": {"C1": [[0, why]]}, "passengers": 0, "delivered": 0,
            "total_time": None, "mean_time": None, "p95_time": None}


def run_one(work, sc, limit):  # old rounds
    made = []

    def factory(floors, lifts):
        # Stored before the constructor can raise, so close() always finds the process.
        d = RemoteDispatcher.__new__(RemoteDispatcher)
        made.append(d)
        d.proc = None
        RemoteDispatcher.__init__(d, work, floors, lifts, limit)
        return d

    try:
        return sim.Simulation(factory, sc).run()
    except TeamStopped as e:
        return stopped_report(sc, str(e))
    finally:
        for d in made:
            if d.proc:
                d.close()


def _bad(report):
    return {k: v for k, v in report["violations"].items() if v}


def judge(repo, upto="v5"):
    """A team's failure is a result. A failure of this tool raises InfraError and isn't scored."""
    work = os.path.realpath(tempfile.mkdtemp(prefix="act3-judge-"))
    result = {"upto": upto, "import_error": None, "hung": False, "scenarios": {}, "q1": {}}
    try:
        shutil.copy(os.path.join(HERE, "team_host.py"), work)
        team = os.path.join(work, "team")
        os.makedirs(team)
        for d in ("dispatcher", "modes"):
            src = os.path.join(repo, d)
            if os.path.isdir(src) and not os.path.islink(src):
                shutil.copytree(src, os.path.join(team, d), symlinks=True,
                                ignore=shutil.ignore_patterns("__pycache__"))
        deadline = time.monotonic() + TOTAL_LIMIT_S

        def timed(sc):
            left = deadline - time.monotonic()
            if left <= 0:
                result["hung"] = True
                return stopped_report(sc, "total compute limit reached")
            r = run_one(work, sc, min(SCENARIO_LIMIT_S, left))
            result["hung"] = result["hung"] or "stopped" in r
            return r

        try:
            for sc in scenarios.all_versions(upto):
                result["scenarios"][sc["name"]] = timed(sc)
            result["q1"] = score_q1(timed)
        except ImportFailed as e:
            result.update(import_error=str(e), scenarios={}, q1={})
        return result
    finally:
        shutil.rmtree(work, ignore_errors=True)


def score_q1(timed):
    """Per batch, so a batch that fails can never improve the average by disappearing."""
    batches, total, optimum = {}, 0, 0
    for sc in scenarios.q1_batches():
        r = timed(sc)
        opt = sim.optimum_onboard(sc["q1"]["start"], sc["q1"]["dests"])
        complete = r["delivered"] == len(sc["q1"]["dests"]) and not _bad(r)
        batches[sc["name"]] = {"complete": complete, "total": r["total_time"], "optimum": opt, "violations": _bad(r)}
        if complete:
            total += r["total_time"]
            optimum += opt
    done = sum(1 for b in batches.values() if b["complete"])
    return {"batches": batches, "complete": done, "incomplete": len(batches) - done, "total_time": total,
            "optimum": optimum, "pct_above_optimum": round(100 * (total - optimum) / optimum, 2) if optimum else None}


# ---- round three -------------------------------------------------------------------------------------------------
RULE_ORDER = ("C1", "S1", "S2", "S3", "L1", "T5", "T5b", "T5c")


def _copy_team(repo, work):
    shutil.copy(os.path.join(HERE, "team_host.py"), work)
    team = os.path.join(work, "team")
    os.makedirs(team)
    for d in ("dispatcher", "modes"):
        src = os.path.join(repo, d)
        if os.path.isdir(src) and not os.path.islink(src):
            shutil.copytree(src, os.path.join(team, d), symlinks=True, ignore=shutil.ignore_patterns("__pycache__"))


def run_day(work, sc, cpu_limit, watchdog):
    """One day on the team's code. `timed_out` says what stopped it, for adjudication: "cpu" or "watchdog"."""
    made, timed = [], False

    def factory(floors, lifts):
        d = RemoteDispatcher.__new__(RemoteDispatcher)
        made.append(d)
        d.proc = None
        RemoteDispatcher.__init__(d, work, floors, lifts, watchdog, cpu_limit)
        return d

    try:
        simulation = sim.Simulation(factory, sc)
        report = simulation.run()
        report["trace"] = hashlib.sha256(json.dumps(simulation.commands_log).encode()).hexdigest()
    except TeamStopped as e:
        report, timed = stopped_report(sc, str(e)), isinstance(e, TeamTimedOut)
    finally:
        for d in made:
            if d.proc:
                d.close()
    cpu = sum(d.cpu_s for d in made)
    report["cpu_s"] = round(cpu, 3)
    if "stopped" in report:
        report["timed_out"] = "watchdog" if timed else ("cpu" if cpu >= cpu_limit - 1 else None)
    return report


def _one_day(task):
    """Runs in a pool worker, or in this process when a day is judged alone: its own folder, its own team process."""
    repo, sc, cpu_limit, watchdog, deny = task
    DENY_READ[:] = deny
    work = os.path.realpath(tempfile.mkdtemp(prefix="act3-day-"))
    try:
        _copy_team(repo, work)
        try:
            return run_day(work, sc, cpu_limit, watchdog)
        except ImportFailed as e:
            return {"scenario": sc["name"], "import_error": str(e)}
        except sim.SimulatorError as e:
            raise InfraError(f"simulator fault on {sc['name']}: {e}") from None
    finally:
        shutil.rmtree(work, ignore_errors=True)


_POOL = None  # one pool per judge_days call, idle whenever a day is being adjudicated


def _run_batch(tasks, workers):
    if workers <= 1 or len(tasks) <= 1 or _POOL is None:
        return [_one_day(t) for t in tasks]
    try:
        return list(_POOL.map(_one_day, tasks))
    except concurrent.futures.process.BrokenProcessPool as e:
        raise InfraError(f"a grading worker died: {e}") from None


def _family_of(sc):
    return sc["name"].split("-")[0]


def _run_family(tasks, workers, result, reports):
    """Batch by batch, so the pool is idle whenever a timeout is adjudicated: nothing else of ours is running then."""
    confirmed = False
    for start in range(0, len(tasks), max(workers, 1)):
        batch = tasks[start:start + max(workers, 1)]
        if confirmed:
            for t in batch:
                reports[t[1]["name"]] = {"scenario": t[1]["name"], "not_run": "family already failed on a confirmed timeout",
                                         "violations": {"C1": 1}}
            continue
        for task, report in zip(batch, _run_batch(batch, workers)):
            if report.get("import_error"):
                result["import_error"] = report["import_error"]
                return
            name = task[1]["name"]
            if report.get("timed_out") and confirmed:
                report = {"scenario": name, "not_run": "family already failed on a confirmed timeout", "violations": {"C1": 1}}
            elif report.get("timed_out"):
                alone = _run_batch([task], 1)[0]
                result["adjudicated"].append({"day": name, "first": report["timed_out"], "alone": alone.get("timed_out")})
                report = alone
                if alone.get("import_error"):
                    result["import_error"] = alone["import_error"]
                    return
                if alone.get("timed_out"):
                    confirmed, result["hung"] = True, True
            reports[name] = report


def judge_days(repo, days, batches=(), workers=6, cpu_limit=DAY_CPU_LIMIT_S, watchdog=DAY_WATCHDOG_S):
    """Round three's judge. A team's failure is a result; a failure of our tools raises InfraError and isn't scored."""
    global _POOL
    if workers <= 1:
        return _judge_days(repo, days, batches, workers, cpu_limit, watchdog)
    context = multiprocessing.get_context("spawn")
    with concurrent.futures.ProcessPoolExecutor(max_workers=workers, mp_context=context) as pool:
        _POOL = pool
        try:
            return _judge_days(repo, days, batches, workers, cpu_limit, watchdog)
        finally:
            _POOL = None


def _judge_days(repo, days, batches, workers, cpu_limit, watchdog):
    result = {"import_error": None, "hung": False, "scenarios": {}, "q1": {}, "adjudicated": [],
              "cpu_limit_s": cpu_limit, "watchdog_s": watchdog}
    deny = list(DENY_READ)
    repo = os.path.realpath(repo)
    families = {}
    for sc in days:
        families.setdefault(_family_of(sc), []).append((repo, sc, cpu_limit, watchdog, deny))
    for family_tasks in families.values():
        _run_family(family_tasks, workers, result, result["scenarios"])
        if result["import_error"]:
            return {**result, "scenarios": {}, "q1": {}}
    if batches:
        q1_reports = {}
        _run_family([(repo, sc, cpu_limit, watchdog, deny) for sc in batches], workers, result, q1_reports)
        if result["import_error"]:
            return {**result, "scenarios": {}, "q1": {}}
        result["q1"] = _score_q1_reports(batches, q1_reports)
        result["q1_traces"] = {name: r.get("trace") for name, r in q1_reports.items()}
    return result


def _score_q1_reports(batches, reports):
    out, total, optimum = {}, 0, 0
    for sc in batches:
        r = reports[sc["name"]]
        opt = sim.optimum_onboard(sc["q1"]["start"], sc["q1"]["dests"])
        complete = r.get("delivered") == len(sc["q1"]["dests"]) and not _bad(r)
        out[sc["name"]] = {"complete": complete, "total": r.get("total_time"), "optimum": opt, "violations": _bad(r)}
        if complete:
            total += r["total_time"]
            optimum += opt
    done = sum(1 for b in out.values() if b["complete"])
    return {"batches": out, "complete": done, "incomplete": len(out) - done, "total_time": total, "optimum": optimum,
            "pct_above_optimum": round(100 * (total - optimum) / optimum, 2) if optimum else None}


def pass_family(result, family, days, batches=()):
    """PASS_k: (True, None), or (False, the first failing day and rule). Anything not measured is a failure."""
    if result.get("import_error"):
        return False, {"day": None, "rule": "import", "detail": result["import_error"][-300:]}
    for sc in days:
        r = result.get("scenarios", {}).get(sc["name"])
        if r is None:
            return False, {"day": sc["name"], "rule": "not measured", "detail": ""}
        bad = _bad(r)
        if bad:
            rule = next((k for k in RULE_ORDER if k in bad), next(iter(bad)))
            return False, {"day": sc["name"], "rule": rule, "detail": str(r.get("examples", {}).get(rule, r.get("stopped", "")))[:200]}
    if family == "v1" and batches:
        got = (result.get("q1") or {}).get("batches") or {}
        for sc in batches:
            if not got.get(sc["name"], {}).get("complete"):
                return False, {"day": sc["name"], "rule": "riders-aboard", "detail": "not everyone delivered"}
    return True, None


def expected_scenarios(upto):
    return [sc["name"] for sc in scenarios.all_versions(upto)]


def acceptance_failures(result, version):
    """Everything standing between this code and "the brief says this version works", earlier
    versions included. Empty only for a complete report; anything missing counts as a failure."""
    if result.get("import_error"):
        return ["the code does not import: " + result["import_error"][-300:]]
    out = []
    for name in expected_scenarios(version):
        r = result.get("scenarios", {}).get(name)
        if r is None:
            out.append(f"{name}: not measured")
        elif _bad(r):
            out.append(f"{name}: {_bad(r)} {str(r.get('examples'))[:160]}")
    got = (result.get("q1") or {}).get("batches") or {}
    expected = [sc["name"] for sc in scenarios.q1_batches()]
    if not got:
        return out + ["riders-aboard runs: not measured"]
    missing = [n for n in expected if n not in got]
    failed = [n for n in expected if n in got and not got[n].get("complete")]
    unknown = [n for n in got if n not in expected]
    if failed:
        out.append(f"riders-aboard runs: {len(failed)} of {len(expected)} failed")
    if missing or unknown:
        out.append(f"riders-aboard report doesn't match: missing {missing[:5]}, unknown {unknown[:5]}")
    return out


def run_team_tests(repo):
    """The team's own test suite, run by us in the same sandbox, so "their tests pass" is a
    captured fact rather than a reviewer's sentence."""
    work = os.path.realpath(tempfile.mkdtemp(prefix="act3-tests-"))
    try:
        copy = os.path.join(work, "repo")
        os.makedirs(copy)
        for d in ("dispatcher", "modes", "tests"):
            src = os.path.join(repo, d)
            if os.path.isdir(src) and not os.path.islink(src):
                shutil.copytree(src, os.path.join(copy, d), symlinks=True,
                                ignore=shutil.ignore_patterns("__pycache__"))
        if not os.path.isdir(os.path.join(copy, "tests")):
            return {"passed": False, "ran": 0, "tail": "no tests folder", "output": ""}
        cmd = ["sandbox-exec", "-p", profile(work), sys.executable, "-m", "unittest", "discover", "-s", "tests"]
        try:
            p = subprocess.Popen(cmd, cwd=copy, env=CLEAN_ENV, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                                 stderr=subprocess.STDOUT, text=True, errors="replace", start_new_session=True)
        except OSError as e:
            raise InfraError(f"could not start the sandbox: {e}") from None
        try:
            out, _ = p.communicate(timeout=TESTS_LIMIT_S)
        except subprocess.TimeoutExpired:
            os.killpg(p.pid, signal.SIGKILL)
            p.communicate()
            return {"passed": False, "ran": 0, "tail": "tests timed out", "output": ""}
        if p.returncode and out.startswith("sandbox-exec:"):
            raise InfraError("sandbox refused to start: " + out[-300:])
        words = [ln.split() for ln in out.splitlines() if ln.startswith("Ran ") and len(ln.split()) > 1 and ln.split()[1].isdigit()]
        ran = int(words[-1][1]) if words else 0
        return {"passed": p.returncode == 0 and ran > 0, "ran": ran, "tail": out[-300:], "output": out[-MAX_OUTPUT_CHARS:]}
    finally:
        shutil.rmtree(work, ignore_errors=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("repo")
    ap.add_argument("--upto", default="v5")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    with open(a.out, "w") as f:
        json.dump(judge(os.path.realpath(a.repo), a.upto), f, indent=1)
