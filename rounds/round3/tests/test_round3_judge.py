"""The round-three path through the judge: sandboxed days, CPU measured apart from the watchdog, timeouts adjudicated
alone, stderr drained, simulator faults kept off the team's score."""
import os
import pathlib
import sys
import tempfile
import unittest
from unittest import mock

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
import judge as J  # noqa: E402
import scenarios_v3 as G  # noqa: E402
import sim  # noqa: E402

BASELINE = pathlib.Path(ROOT, "baselines.py").read_text()
REFERENCE = BASELINE.split("class OptimalOnboard")[0].replace("class Baseline:", "class Dispatcher:")
ALL_BROKEN = "import itertools\n" + BASELINE.split('"""', 2)[2].split("import itertools", 1)[1]


def repo(source):
    d = tempfile.TemporaryDirectory(prefix="r3-judge-")
    p = pathlib.Path(d.name, "dispatcher")
    p.mkdir()
    (p / "__init__.py").write_text(source)
    return d


def broken(name):
    return ALL_BROKEN + f"\nDispatcher = {name}\n"


def sample(per_family=2, families=("v1", "v2", "v3", "v4", "v5")):
    return [G.scenario(f, 1000 + i) for f in families for i in range(per_family)]


class Reference(unittest.TestCase):
    def test_reference_passes_each_family_through_the_sandbox(self):
        with repo(REFERENCE) as d:
            days = sample()
            result = J.judge_days(d, days, G.q1_batches()[:3], workers=3)
        self.assertIsNone(result["import_error"])
        self.assertFalse(result["hung"])
        self.assertEqual(result["adjudicated"], [])
        for fam in ("v1", "v2", "v3", "v4", "v5"):
            mine = [s for s in days if s["name"].startswith(fam)]
            ok, why = J.pass_family(result, fam, mine, G.q1_batches()[:3])
            self.assertTrue(ok, (fam, why))

    def test_parallel_and_serial_judging_agree_exactly(self):
        days = sample(1)
        with repo(REFERENCE) as d:
            a = J.judge_days(d, days, G.q1_batches()[:2], workers=1)
            b = J.judge_days(d, days, G.q1_batches()[:2], workers=4)
        for name in a["scenarios"]:
            for key in ("violations", "trace", "max_time", "lobby_p95", "rush_upper_max", "completions"):
                self.assertEqual(a["scenarios"][name][key], b["scenarios"][name][key], (name, key))
        self.assertEqual(a["q1"]["batches"], b["q1"]["batches"])

    def test_sandboxed_run_equals_the_in_process_run(self):
        import baselines
        sc = G.scenario("v4", 5)
        direct = sim.Simulation(baselines.Baseline, sc).run()
        with repo(REFERENCE) as d:
            remote = J.judge_days(d, [sc], (), workers=1)["scenarios"][sc["name"]]
        for key in ("violations", "max_time", "total_time", "completions"):
            self.assertEqual(direct[key], remote[key], key)


class Timing(unittest.TestCase):
    def test_the_old_total_deadline_does_not_apply(self):
        with repo(REFERENCE) as d, mock.patch.object(J, "TOTAL_LIMIT_S", 0):
            result = J.judge_days(d, sample(1, ("v1",)), (), workers=1)
        self.assertFalse(result["hung"])
        self.assertEqual(sum(result["scenarios"]["v1-1000"]["violations"].values()), 0)

    def test_cpu_is_measured_and_reported_per_day(self):
        with repo(REFERENCE) as d:
            r = J.judge_days(d, sample(1, ("v1",)), (), workers=1)["scenarios"]["v1-1000"]
        self.assertGreater(r["cpu_s"], 0)

    def test_a_cpu_hog_is_stopped_by_cpu_not_wall_clock_and_confirmed_alone(self):
        source = REFERENCE + "\n    def on_call(self, t, floor, direction):\n        while True:\n            pass\n"
        sc = G.scenario("v1", 1)
        with repo(source) as d:
            result = J.judge_days(d, [sc], (), workers=1, cpu_limit=1, watchdog=60)
        r = result["scenarios"][sc["name"]]
        self.assertIn("stopped", r)
        self.assertEqual(r["timed_out"], "cpu")
        self.assertTrue(result["hung"])
        self.assertEqual(result["adjudicated"][0]["alone"], "cpu")
        self.assertFalse(J.pass_family(result, "v1", [sc], ())[0])

    def test_a_silent_hang_hits_the_watchdog_and_is_confirmed_alone(self):
        source = "import time\n" + REFERENCE + "\n    def on_call(self, t, floor, direction):\n        time.sleep(100)\n"
        sc = G.scenario("v1", 1)
        with repo(source) as d:
            result = J.judge_days(d, [sc], (), workers=1, cpu_limit=30, watchdog=1)
        self.assertEqual(result["scenarios"][sc["name"]]["timed_out"], "watchdog")
        self.assertEqual(result["adjudicated"][0]["alone"], "watchdog")

    def test_a_timeout_that_clears_alone_counts_as_the_clean_run(self):
        sc = G.scenario("v1", 1)
        first = J.stopped_report(sc, "watchdog")
        first.update(timed_out="watchdog", cpu_s=0.1)
        real = J._run_batch
        calls = []

        def fake(tasks, workers):
            calls.append(workers)
            if len(calls) == 1:
                return [first]
            return real(tasks, workers)
        with repo(REFERENCE) as d, mock.patch.object(J, "_run_batch", fake):
            result = J.judge_days(d, [sc], (), workers=4)
        self.assertEqual(calls[1], 1, "the adjudication runs alone")
        self.assertEqual(result["adjudicated"], [{"day": sc["name"], "first": "watchdog", "alone": None}])
        self.assertFalse(result["hung"])
        self.assertNotIn("stopped", result["scenarios"][sc["name"]])
        self.assertTrue(J.pass_family(result, "v1", [sc], ())[0])

    def test_a_confirmed_timeout_ends_the_family_but_not_the_others(self):
        days = [G.scenario("v1", i) for i in range(4)] + [G.scenario("v2", 1)]

        def fake(tasks, workers):
            out = []
            for t in tasks:
                sc = t[1]
                if sc["name"].startswith("v1"):
                    r = J.stopped_report(sc, "hung")
                    r.update(timed_out="watchdog", cpu_s=0.0)
                else:
                    r = J.stopped_report(sc, "")
                    r.pop("stopped")
                    r["violations"]["C1"] = 0
                out.append(r)
            return out
        with repo(REFERENCE) as d, mock.patch.object(J, "_run_batch", fake):
            result = J.judge_days(d, days, (), workers=2)
        self.assertEqual(len(result["adjudicated"]), 1)
        self.assertEqual(result["scenarios"]["v1-2"]["not_run"], "family already failed on a confirmed timeout")
        self.assertTrue(J.pass_family(result, "v2", days[4:], ())[0])
        ok, why = J.pass_family(result, "v1", days[:4], ())
        self.assertFalse(ok)
        self.assertEqual(why["day"], "v1-0")


class Stderr(unittest.TestCase):
    def test_a_dispatcher_logging_every_tick_does_not_hang(self):
        source = "import sys\n" + REFERENCE + ("\n    _step = step\n    def step(self, t, floors_now):\n"
                                               "        sys.stderr.write('x' * 4096 + chr(10))\n        sys.stderr.flush()\n"
                                               "        return self._step(t, floors_now)\n")
        sc = G.scenario("v1", 1)
        with repo(source) as d:
            result = J.judge_days(d, [sc], (), workers=1, cpu_limit=30, watchdog=30)
        r = result["scenarios"][sc["name"]]
        self.assertNotIn("stopped", r)
        self.assertEqual(sum(r["violations"].values()), 0)


class Isolation(unittest.TestCase):
    def test_judged_code_can_not_read_a_denied_folder(self):
        with tempfile.TemporaryDirectory(prefix="r3-room-") as other:
            secret = pathlib.Path(other, "secret.txt")
            secret.write_text("x")
            source = REFERENCE + (f"\n    _init = __init__\n    def __init__(self, floors, lifts):\n"
                                  f"        self._init(floors, lifts)\n        open({str(secret)!r}).read()\n")
            with repo(source) as d, mock.patch.object(J, "DENY_READ", [other]):
                result = J.judge_days(d, sample(1, ("v1",)), (), workers=1)
            self.assertGreater(result["scenarios"]["v1-1000"]["violations"]["C1"], 0)
            with repo(source) as d, mock.patch.object(J, "DENY_READ", []):
                result = J.judge_days(d, sample(1, ("v1",)), (), workers=1)
            self.assertEqual(result["scenarios"]["v1-1000"]["violations"]["C1"], 0)


class Failures(unittest.TestCase):
    def test_import_error_fails_every_family(self):
        with repo("raise RuntimeError('nope')\n") as d:
            days = sample(1)
            result = J.judge_days(d, days, (), workers=2)
        self.assertIn("nope", result["import_error"])
        ok, why = J.pass_family(result, "v3", days, ())
        self.assertFalse(ok)
        self.assertEqual(why["rule"], "import")

    def test_no_code_is_a_failure_not_a_crash(self):
        with tempfile.TemporaryDirectory() as d:
            result = J.judge_days(d, sample(1, ("v1",)), (), workers=1)
        self.assertTrue(result["import_error"])

    def test_a_simulator_fault_is_infrastructure_never_the_team(self):
        class Faulty(sim.Simulation):
            def _conserve(self, t):
                raise sim.SimulatorError("planted")
        with repo(REFERENCE) as d, mock.patch.object(J.sim, "Simulation", Faulty):
            with self.assertRaises(J.InfraError):
                J.judge_days(d, sample(1, ("v1",)), (), workers=1)

    def test_missing_day_is_a_failure(self):
        sc = G.scenario("v1", 1)
        ok, why = J.pass_family({"import_error": None, "scenarios": {}, "q1": {}}, "v1", [sc], ())
        self.assertFalse(ok)
        self.assertEqual(why["rule"], "not measured")

    def test_v1_needs_all_batches(self):
        sc = G.scenario("v1", 1)
        batches = G.q1_batches()[:1]
        report = {"violations": {"C1": 0}}
        good = {"import_error": None, "scenarios": {sc["name"]: report}, "q1": {"batches": {batches[0]["name"]: {"complete": True}}}}
        self.assertTrue(J.pass_family(good, "v1", [sc], batches)[0])
        bad = {**good, "q1": {"batches": {batches[0]["name"]: {"complete": False}}}}
        self.assertEqual(J.pass_family(bad, "v1", [sc], batches)[1]["rule"], "riders-aboard")
        none = {**good, "q1": {}}
        self.assertEqual(J.pass_family(none, "v1", [sc], batches)[1]["rule"], "riders-aboard")

    def test_each_rush_measure_fails_the_family(self):
        sc = G.scenario("v5", 1)
        for rule in ("T5b", "T5c"):
            result = {"import_error": None, "scenarios": {sc["name"]: {"violations": {rule: 1}}}, "q1": {}}
            ok, why = J.pass_family(result, "v5", [sc], ())
            self.assertFalse(ok)
            self.assertEqual(why["rule"], rule)


class BrokenDispatchers(unittest.TestCase):
    EXPECT = {"IgnoresFire": "S2", "MovesWhileOutOfService": "S3", "WrongCommandCount": "C1",
              "FallsThroughFloor": "S1", "OnlyCarCalls": "L1"}

    def test_each_broken_dispatcher_fails_the_rule_it_breaks(self):
        days = sample(3)
        for name, rule in self.EXPECT.items():
            with repo(broken(name)) as d:
                result = J.judge_days(d, days, (), workers=6)
            seen = {k for r in result["scenarios"].values() for k, v in r["violations"].items() if v}
            self.assertIn(rule, seen, name)
            self.assertTrue(any(not J.pass_family(result, f, [s for s in days if s["name"].startswith(f)], ())[0]
                                for f in ("v1", "v2", "v3", "v4", "v5")), name)


if __name__ == "__main__":
    unittest.main()
