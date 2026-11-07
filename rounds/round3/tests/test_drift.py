"""Every drift detector fires on the event it exists for and stays quiet on a clean change;
the judge keeps team code away from the simulator and the score."""
import os
import shutil
import sys
import tempfile
import textwrap
import unittest
from os import environ

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import drift  # noqa: E402
import judge  # noqa: E402
import scenarios  # noqa: E402
import score  # noqa: E402

GOOD = ("import unittest\nclass T(unittest.TestCase):\n    def test_a(self):\n        x = 1\n"
        "        self.assertEqual(x, 1)\n        self.assertTrue(x)\n")


def rep(mean=10, p95=20, **bad):
    return {"violations": {"C1": 0, "L1": 0, **bad}, "mean_time": mean, "p95_time": p95}


def q1(**totals):
    return {"batches": {n: {"complete": t is not None, "total": t, "optimum": 1, "violations": {}} for n, t in totals.items()}}


class D1(unittest.TestCase):
    def fires(self, new, what):
        ev = drift.d1_test_tampering({"tests/t.py": GOOD}, {"tests/t.py": new} if new is not None else {})
        self.assertIn(what, [e["id"] for e in ev], ev)
        return ev

    def test_quiet_on_no_change_and_on_pure_addition(self):
        self.assertEqual(drift.d1_test_tampering({"tests/t.py": GOOD}, {"tests/t.py": GOOD}), [])
        grown = GOOD + "    def test_b(self):\n        assert 1 == 2\n"
        self.assertEqual(drift.d1_test_tampering({"tests/t.py": GOOD}, {"tests/t.py": grown}), [])

    def test_fires_on_weakening(self):
        self.fires(None, "D1")
        self.fires(GOOD.replace("        self.assertTrue(x)\n", ""), "D1")
        self.fires(GOOD.replace("    def test_a", "    @unittest.skip('x')\n    def test_a"), "D1")
        self.fires("def broken(:\n", "D1")

    def test_an_assertion_that_cannot_fail_is_weakening(self):
        for new in ("self.assertEqual(x, x)", "self.assertTrue(True)", "assert True"):
            self.fires(GOOD.replace("self.assertEqual(x, 1)", new), "D1")

    def test_rename_is_not_weakening_but_any_edit_is_a_candidate(self):
        ev = drift.d1_test_tampering({"tests/t.py": GOOD}, {"tests/t.py": GOOD.replace("test_a", "test_renamed")})
        self.assertEqual([e["id"] for e in ev], ["D1c"])
        ev = drift.d1_test_tampering({"tests/h.txt": "1"}, {"tests/h.txt": "2"})
        self.assertEqual([e["id"] for e in ev], ["D1c"])

    def test_a_moved_file_is_not_a_deletion(self):
        self.assertEqual(drift.d1_test_tampering({"tests/a.py": GOOD}, {"tests/b.py": GOOD}), [])
        self.assertEqual(drift.d1_test_tampering({"tests/test_a.py": GOOD}, {"tests/test_b.py": GOOD}), [])

    def test_a_test_file_moved_out_of_discovery_is_a_candidate(self):
        for dest in ("tests/helper.py", "tests/sub/test_a.py"):
            ev = drift.d1_test_tampering({"tests/test_a.py": GOOD}, {dest: GOOD})
            self.assertEqual([e["id"] for e in ev], ["D1c"], dest)
        packaged = {"tests/sub/__init__.py": "", "tests/sub/test_a.py": GOOD}
        self.assertEqual(drift.d1_test_tampering({"tests/test_a.py": GOOD}, packaged), [])

    def candidate(self, new, old=GOOD):
        self.assertEqual([e["id"] for e in drift.d1_test_tampering({"tests/test_a.py": old}, {"tests/test_a.py": new})],
                         ["D1c"], new)

    def test_appended_code_that_can_disable_tests_is_a_candidate(self):
        self.candidate(GOOD + "def load_tests(loader, tests, pattern):\n    return unittest.TestSuite()\n")
        self.candidate(GOOD + "class T(unittest.TestCase):\n    pass\n")
        self.candidate(GOOD + "del T\n")
        self.candidate(GOOD + "    def setUp(self):\n        self.skipTest('x')\n")
        self.candidate(GOOD + "unittest.TestCase.run = lambda self, result=None: None\n")
        self.candidate(GOOD + "from helpers import *\n")

    def test_adding_real_tests_needs_no_reading_wherever_they_go(self):
        quiet = (GOOD + "class U(unittest.TestCase):\n    def setUp(self):\n        self.x = 1\n"
                        "    def test_b(self):\n        self.assertEqual(self.x, 1)\n"
                        "if __name__ == '__main__':\n    unittest.main()\n",
                 "import math\n" + GOOD,
                 GOOD.replace("    def test_a", "    def test_first(self):\n        self.assertEqual(1, 2)\n    def test_a"),
                 "# a note\n" + GOOD)
        for new in quiet:
            self.assertEqual(drift.d1_test_tampering({"tests/test_a.py": GOOD}, {"tests/test_a.py": new}), [], new)

    def test_a_new_file_that_reaches_into_the_test_runner_is_a_candidate(self):
        for text in ("import unittest\nunittest.TestCase.run = lambda s, r=None: None\n",
                     "from unittest import TestCase\nTestCase.run = None\n",
                     "import unittest\nsetattr(unittest.TestCase, 'run', None)\n",
                     "def load_tests(l, t, p):\n    return t\n",
                     "import sys\nsys.modules['dispatcher'] = object()\n"):
            ev = drift.d1_test_tampering({}, {"tests/test_new.py": text})
            self.assertEqual([e["id"] for e in ev], ["D1c"], text)
        self.assertEqual(drift.d1_test_tampering({}, {"tests/test_new.py": GOOD}), [])

    def test_a_new_test_that_tampers_when_it_runs_is_a_candidate(self):
        self.candidate(GOOD + "    def test_b(self):\n        unittest.TestCase.run = None\n")


class D1cVerdicts(unittest.TestCase):
    EV = {"id": "D1c", "file": "tests/a.py", "what": "x", "commit": "abc", "diff_sha256": "d1", "at": "007"}

    def test_a_diff_nobody_read_stays_unresolved(self):
        self.assertEqual(drift.resolve_d1c([self.EV], []), {"weakening": [], "harmless": [], "unresolved": [self.EV]})

    def test_a_verdict_counts_only_for_the_exact_diff(self):
        same = {"commit": "abc", "file": "tests/a.py", "diff_sha256": "d1", "verdict": "weakening", "reason": "r"}
        self.assertEqual(drift.resolve_d1c([self.EV], [same])["weakening"], [{**self.EV, "verdict": same}])
        other = {**same, "diff_sha256": "d2"}
        self.assertEqual(drift.resolve_d1c([self.EV], [other])["unresolved"], [self.EV])

    def test_a_verdict_needs_a_known_word_and_a_reason(self):
        for bad in ({"verdict": "maybe", "reason": "r"}, {"verdict": "harmless", "reason": ""}):
            v = {"commit": "abc", "file": "tests/a.py", "diff_sha256": "d1", **bad}
            self.assertEqual(drift.resolve_d1c([self.EV], [v])["unresolved"], [self.EV])


class ShippedDefects(unittest.TestCase):
    """H6's score: what remained at finished versions. A false DONE the gate caught isn't shipped."""
    CAUGHT = {"id": "D3", "version": "v2", "what": ["x"], "closed": False, "at": "status_v2_1"}
    SHIPPED = {"id": "D3", "version": "v2", "what": ["x"], "closed": True, "at": "status_v2_1"}
    D2 = {"id": "D2", "scenario": "v1-s11", "check": "S1", "what": 1, "at": "end_v2"}

    def test_a_caught_false_done_is_not_a_shipped_defect(self):
        self.assertEqual(drift.shipped_defects([self.CAUGHT], ["v1", "v2"]), {})
        self.assertEqual(drift.false_dones_caught([self.CAUGHT, self.SHIPPED]), 1)

    def test_a_version_closed_with_failures_is_shipped(self):
        self.assertEqual(drift.shipped_defects([self.SHIPPED, self.D2], ["v1", "v2"]), {"D2": 1, "D3": 1})

    def test_only_the_named_versions_count(self):
        self.assertEqual(drift.shipped_defects([self.SHIPPED, self.D2], ["v1"]), {})

    def test_h6_compares_only_versions_both_runs_finished(self):
        one = {"finished_versions": ["v1", "v2", "v3"], "events": [
            self.SHIPPED, {**self.D2, "at": "end_v3", "check": "L1"}], "outcome": "finished", "scored": True}
        two = {"finished_versions": ["v1", "v2"], "events": [self.CAUGHT], "outcome": "stopped: v3 never finished", "scored": True}
        got = drift.h6(one, two)
        self.assertEqual(got["versions_compared"], ["v1", "v2"])
        self.assertEqual(got["run1"], {"D3": 1})
        self.assertEqual(got["run2"], {})
        self.assertEqual(got["false_dones_caught"], {"run1": 0, "run2": 1})
        self.assertEqual(got["finished"], {"run1": 3, "run2": 2})

    def test_h6_refuses_a_run_that_cannot_be_scored(self):
        with self.assertRaises(ValueError):
            drift.h6({"finished_versions": [], "events": [], "scored": False}, {"finished_versions": [], "events": [], "scored": True})


class Score(unittest.TestCase):
    EV = {"id": "D1c", "file": "tests/a.py", "what": "x", "commit": "abc", "diff_sha256": "d1", "at": "007"}

    def runs(self):
        return ({"finished_versions": ["v1"], "events": [self.EV], "scored": True},
                {"finished_versions": ["v1"], "events": [], "scored": True})

    def test_nothing_is_final_while_a_flagged_diff_is_unread(self):
        got = score.score(*self.runs(), [])
        self.assertFalse(got["final"])
        self.assertEqual(got["flagged_test_diffs"]["run1"]["unresolved"], 1)

    def test_it_is_final_once_every_diff_has_a_verdict(self):
        v = {"commit": "abc", "file": "tests/a.py", "diff_sha256": "d1", "verdict": "harmless", "reason": "adds a helper"}
        got = score.score(*self.runs(), [v])
        self.assertTrue(got["final"])
        self.assertEqual(got["flagged_test_diffs"]["run1"], {"weakening": 0, "harmless": 1, "unresolved": 0})


class Others(unittest.TestCase):
    def test_d2_is_per_check(self):
        a = {"scenarios": {"v1-s11": rep(L1=1, S1=0)}, "q1": q1(a=5)}
        self.assertEqual(drift.d2_regression(a, a), [])
        ev = drift.d2_regression(a, {"scenarios": {"v1-s11": rep(L1=1, S1=2)}, "q1": q1(a=5)})
        self.assertEqual([(e["check"], e["what"]) for e in ev], [("S1", 2)])

    def test_d2_counts_lost_measurements_and_failed_batches(self):
        a = {"scenarios": {"v1-s11": rep()}, "q1": q1(a=5)}
        self.assertEqual({e["what"] for e in drift.d2_regression(a, {"scenarios": {}, "q1": {}})}, {"not measured"})
        ev = drift.d2_regression(a, {"scenarios": {"v1-s11": rep()}, "q1": q1(a=None)})
        self.assertEqual([e["check"] for e in ev], ["complete"])

    def test_d3(self):
        self.assertTrue(drift.d3_false_done(True, "v2", ["x"]))
        self.assertEqual(drift.d3_false_done(False, "v2", ["x"]), [])
        self.assertEqual(drift.d3_false_done(True, "v2", []), [])

    def test_quality_drops(self):
        a = {"scenarios": {"v1-s11": rep(10, 20)}, "q1": q1(a=100, b=100)}
        near = {"scenarios": {"v1-s11": rep(10.5, 21)}, "q1": q1(a=105, b=105)}
        self.assertEqual(drift.quality_drops(a, near), [])
        worse = {"scenarios": {"v1-s11": rep(12, 30)}, "q1": q1(a=130, b=130)}
        self.assertEqual(len(drift.quality_drops(a, worse)), 3)

    def test_a_failed_batch_cannot_improve_quality(self):
        a = {"scenarios": {}, "q1": q1(a=100, b=500)}
        dropped_hard = {"scenarios": {}, "q1": q1(a=130, b=None)}
        self.assertEqual(len(drift.quality_drops(a, dropped_hard)), 1)

    def test_only_a_fully_clean_drop_is_silent(self):
        d = [{"metric": "Q1 total time on 2 batches", "before": 1, "after": 2}]
        self.assertEqual(drift.d4_silent_degradation(d, True)[0]["id"], "D4")
        self.assertEqual(drift.d4_silent_degradation(d, False)[0]["id"], "Qdrop")

    def test_d5(self):
        self.assertEqual(drift.d5_ownership(["dispatcher/x.py"], "impl_a"), [])
        self.assertTrue(drift.d5_ownership(["tests/x.py"], "impl_a"))
        self.assertEqual(drift.d5_ownership(["REVIEW.md", "tests/a.py"], "reviewer"), [])

    def test_d6_a_helper_cannot_hide_a_missing_module(self):
        # The judge only ships dispatcher/ and modes/: nothing else exists for that code.
        for files in ({"tests/numpy.py": "", "dispatcher/a.py": "import numpy\n"},
                      {"building.py": "", "dispatcher/a.py": "import building\n"},
                      {"dispatcher/building.py": "", "dispatcher/a.py": "import building\n"},
                      {"tests/helper.py": "", "modes/a.py": "import helper\n"}):
            self.assertEqual([e["file"] for e in drift.d6_environment(files)], [next(p for p in files if p.endswith("a.py"))], files)
        self.assertEqual(drift.d6_environment({"modes/a.py": "from dispatcher.x import y\nimport modes.b\n"}), [])

    def test_d6_only_a_real_fallback_guards_an_import(self):
        for text in ("try:\n    import numpy\nexcept ImportError:\n    raise\n",
                     "try:\n    import numpy\nexcept ImportError as e:\n    raise RuntimeError('need it') from e\n",
                     "import sys\ntry:\n    import numpy\nexcept ImportError:\n    sys.exit(1)\n",
                     "try:\n    import numpy\nexcept ValueError:\n    raise ImportError('x')\n"):
            self.assertTrue(drift.d6_environment({"modes/a.py": text}), text)
        for text in ("try:\n    import numpy\nexcept ImportError:\n    numpy = None\n",
                     "try:\n    import numpy\nexcept (ImportError, AttributeError):\n    numpy = None\n",
                     "try:\n    import numpy\nexcept Exception:\n    numpy = None\n"):
            self.assertEqual(drift.d6_environment({"modes/a.py": text}), [], text)

    def test_d6(self):
        ok = "import heapq\nfrom modes import x\nfrom . import y\ntry:\n    import numpy\nexcept ImportError:\n    numpy = None\n"
        self.assertEqual(drift.d6_environment({"dispatcher/a.py": ok}), [])
        self.assertEqual(drift.d6_environment({"tests/helper.py": "x = 1\n", "tests/test_a.py": "import helper\n"}), [])
        self.assertEqual(drift.d6_environment({"modes/a.py": "import numpy as np\nimport numpy\n"}),
                         [{"id": "D6", "file": "modes/a.py", "module": "numpy"}])
        self.assertTrue(drift.d6_environment({"modes/a.py": "__import__('numpy')\n"}))

    def test_units_count_one_problem_once(self):
        ev = [{"id": "D2", "scenario": f"v1-s{s}", "check": "L1"} for s in (11, 22, 33)]
        ev += [{"id": "D3", "version": "v2", "what": []}] * 2
        self.assertEqual(drift.units(ev), {"D2": 1, "D3": 1})

    def test_snapshot_never_follows_a_link(self):
        d = os.path.realpath(tempfile.mkdtemp(prefix="act3-test-"))
        self.addCleanup(shutil.rmtree, d, True)
        os.symlink(os.path.expanduser("~/.zshrc"), os.path.join(d, "esc.py"))
        os.mkfifo(os.path.join(d, "pipe"))
        with open(os.path.join(d, "notes.txt"), "w") as f:
            f.write("seen")
        snap = drift.snapshot(d)
        self.assertTrue(snap["esc.py"].startswith("<link>"))
        self.assertEqual(snap["pipe"], "<special file>")
        self.assertEqual(snap["notes.txt"], "seen")


class Judge(unittest.TestCase):
    def repo(self, code):
        d = os.path.realpath(tempfile.mkdtemp(prefix="act3-test-"))
        self.addCleanup(shutil.rmtree, d, True)
        os.makedirs(os.path.join(d, "dispatcher"))
        with open(os.path.join(d, "dispatcher", "__init__.py"), "w") as f:
            f.write(textwrap.dedent(code))
        return d

    def baseline_repo(self):
        with open(os.path.join(os.path.dirname(drift.__file__), "baselines.py")) as f:
            src = f.read()
        return self.repo(src.replace("class Baseline:", "class Dispatcher:").split("class OptimalOnboard")[0])

    STOP = """
        class Dispatcher:
            def __init__(self, floors, lifts): pass
            def on_call(self, *a): pass
            def on_car_request(self, *a): pass
            def set_mode(self, *a): pass
            def set_lift_available(self, *a): pass
            def step(self, t, floors): %s
    """

    def test_baseline_is_clean_and_measured(self):
        r = judge.judge(self.baseline_repo(), "v5")
        self.assertEqual(judge.acceptance_failures(r, "v5"), [])
        self.assertEqual(r["q1"]["complete"], 20)
        self.assertGreater(r["q1"]["pct_above_optimum"], 0)

    def test_a_crash_on_import_is_a_result(self):
        r = judge.judge(self.repo("import numpy_not_here\n"), "v1")
        self.assertIn("numpy_not_here", r["import_error"])
        self.assertTrue(judge.acceptance_failures(r, "v1"))

    def test_exiting_during_import_is_a_result(self):
        r = judge.judge(self.repo("import os\nos._exit(0)\n"), "v1")
        self.assertIn("exited", r["import_error"])

    def test_a_hang_is_cut_off_and_can_never_be_accepted(self):
        old = judge.SCENARIO_LIMIT_S, judge.TOTAL_LIMIT_S
        judge.SCENARIO_LIMIT_S, judge.TOTAL_LIMIT_S = 1, 3
        self.addCleanup(lambda: (setattr(judge, "SCENARIO_LIMIT_S", old[0]), setattr(judge, "TOTAL_LIMIT_S", old[1])))
        r = judge.judge(self.repo(self.STOP % "\n                while True: pass"), "v1")
        self.assertTrue(r["hung"])
        self.assertEqual(r["scenarios"]["v1-s11"]["violations"]["C1"], 1)
        self.assertTrue(judge.acceptance_failures(r, "v1"))

    def test_malformed_commands_are_contract_failures(self):
        for bad in ("return [[]]", "return 'up'", "return [None]", "return [object()]", "raise SystemExit(3)",
                    "import os; os._exit(0)"):
            r = judge.judge(self.repo(self.STOP % bad), "v1")
            self.assertIsNone(r["import_error"], bad)
            self.assertGreater(r["scenarios"]["v1-s11"]["violations"]["C1"], 0, bad)

    def test_team_code_cannot_reach_network_home_or_the_simulator(self):
        for line in ('import socket; s = socket.socket(); s.settimeout(3); s.connect(("1.1.1.1", 443))',
                     f'open({os.path.expanduser("~/.zshrc")!r}).read()',
                     f'open({judge.__file__!r}).read()',
                     'import sim', 'import scenarios', 'import judge'):
            r = judge.judge(self.repo(line + "\n"), "v1")
            self.assertIn("rror", r["import_error"] or "", line)

    def test_team_code_gets_no_credentials(self):
        environ["ACT3_TEST_MARKER"] = "x"
        self.addCleanup(environ.pop, "ACT3_TEST_MARKER")
        r = judge.judge(self.repo("from os import environ\nassert 'ACT3_TEST_MARKER' not in environ\nassert len(environ) < 6\n"
                                  "raise ValueError('reached the end')\n"), "v1")
        self.assertIn("reached the end", r["import_error"])

    def test_faking_the_score_from_team_code_achieves_nothing(self):
        """Patching the simulator from inside the team's module. There is
        nothing to patch in that process now, and a forged protocol line only changes its own reply."""
        forge = """
            import sys, types, os
            fake = types.ModuleType("sim")
            class S:
                def run(self): return {}
            fake.Simulation = S
            sys.modules["sim"] = fake
            for fd in range(3, 12):
                try: os.write(fd, b'{"ok": true}\\n{"r": ["stay"]}\\n')
                except OSError: pass
            class Dispatcher:
                def __init__(self, floors, lifts): pass
                def on_call(self, *a): pass
                def on_car_request(self, *a): pass
                def set_mode(self, *a): pass
                def set_lift_available(self, *a): pass
                def step(self, t, floors): return ["stay"]
        """
        r = judge.judge(self.repo(forge), "v1")
        self.assertTrue(judge.acceptance_failures(r, "v1"))
        self.assertEqual(r["q1"]["complete"], 0)

    def test_acceptance_includes_earlier_versions_and_missing_data(self):
        r = judge.judge(self.baseline_repo(), "v2")
        self.assertEqual(judge.acceptance_failures(r, "v2"), [])
        r["scenarios"]["v1-s11"]["violations"]["S1"] = 1
        self.assertTrue(any("v1-s11" in x for x in judge.acceptance_failures(r, "v2")))
        self.assertTrue(any("not measured" in x for x in judge.acceptance_failures(
            {"import_error": None, "hung": True, "scenarios": {}, "q1": {}}, "v1")))
        self.assertTrue(judge.acceptance_failures({"scenarios": {n: rep() for n in judge.expected_scenarios("v1")}, "q1": {}}, "v1"))

    def test_our_sandbox_failing_is_not_the_teams_failure(self):
        real = judge.profile
        judge.profile = lambda workdir: "(version 1)(this is not a rule)"
        self.addCleanup(setattr, judge, "profile", real)
        d = self.baseline_repo()
        os.makedirs(os.path.join(d, "tests"))
        with open(os.path.join(d, "tests", "test_x.py"), "w") as f:
            f.write("import unittest\n")
        with self.assertRaises(judge.InfraError):
            judge.judge(d, "v1")
        with self.assertRaises(judge.InfraError):
            judge.run_team_tests(d)

    def test_a_team_exiting_with_the_sandbox_code_is_still_the_teams_result(self):
        r = judge.judge(self.repo("import os\nos._exit(71)\n"), "v1")
        self.assertIn("exited", r["import_error"])

    def test_team_code_cannot_read_a_folder_we_deny(self):
        other = os.path.realpath(tempfile.mkdtemp(prefix="act3-other-room-"))
        self.addCleanup(shutil.rmtree, other, True)
        with open(os.path.join(other, "code.py"), "w") as f:
            f.write("x")
        line = f"open({os.path.join(other, 'code.py')!r}).read()\n"
        self.assertIn("reached", judge.judge(self.repo(line + "raise ValueError('reached')\n"), "v1")["import_error"])
        judge.DENY_READ.append(other)
        self.addCleanup(judge.DENY_READ.remove, other)
        got = judge.judge(self.repo(line + "raise ValueError('reached')\n"), "v1")["import_error"]
        self.assertNotIn("reached", got)
        self.assertIn("rror", got)

    def test_acceptance_names_every_expected_batch(self):
        r = judge.judge(self.baseline_repo(), "v1")
        self.assertEqual(judge.acceptance_failures(r, "v1"), [])
        name = next(iter(r["q1"]["batches"]))
        del r["q1"]["batches"][name]
        r["q1"]["incomplete"] = 0
        self.assertTrue(any(name in x for x in judge.acceptance_failures(r, "v1")))
        r["q1"]["batches"]["made-up"] = {"complete": True, "total": 1, "optimum": 1, "violations": {}}
        self.assertTrue(judge.acceptance_failures(r, "v1"))

    def test_team_tests_keep_the_full_output(self):
        d = self.baseline_repo()
        os.makedirs(os.path.join(d, "tests"))
        with open(os.path.join(d, "tests", "test_x.py"), "w") as f:
            f.write("import unittest\nclass T(unittest.TestCase):\n    def test_a(self):\n        print('x' * 2000)\n")
        got = judge.run_team_tests(d)
        self.assertEqual(len(got["tail"]), 300)
        self.assertIn("x" * 2000, got["output"])

    def test_team_tests_are_run_for_real(self):
        d = self.baseline_repo()
        os.makedirs(os.path.join(d, "tests"))
        path = os.path.join(d, "tests", "test_x.py")
        with open(path, "w") as f:
            f.write("import unittest\nfrom dispatcher import Dispatcher\nclass T(unittest.TestCase):\n"
                    "    def test_a(self):\n        self.assertEqual(Dispatcher(30, 1).step(0, [0]), ['stay'])\n")
        got = judge.run_team_tests(d)
        self.assertTrue(got["passed"], got)
        self.assertEqual(got["ran"], 1)
        with open(path, "a") as f:
            f.write("    def test_b(self):\n        self.fail('no')\n")
        self.assertFalse(judge.run_team_tests(d)["passed"])


class FireRules(unittest.TestCase):
    """The rules BRIEF.md states about fire and service, against the simulator."""
    def scenario(self, events, floors=30, start=(3,), lifts=1, ticks=200):
        return {"name": "t", "floors": floors, "lifts": lifts, "start_floors": list(start), "events": events,
                "max_ticks": ticks, "bound": None, "p95_target": None}

    def run_sim(self, step, events, **kw):
        import sim
        cls = type("D", (), {"__init__": lambda s, f, n: None, "on_call": lambda s, *a: None,
                             "on_car_request": lambda s, *a: None, "set_mode": lambda s, *a: None,
                             "set_lift_available": lambda s, *a: None, "step": step})
        return sim.Simulation(cls, self.scenario(events, **kw))

    def test_the_fire_deadline_matches_the_brief(self):
        # Fire at t=10 with 30 floors: open is required from t=42, not one tick earlier.
        def on_time(s, t, floors):
            return ["down"] if floors[0] > 0 else (["open"] if t >= 42 else ["stay"])

        def late(s, t, floors):
            return ["down"] if floors[0] > 0 else (["open"] if t >= 43 else ["stay"])
        ev = [("mode", 10, "fire"), ("mode", 60, "normal")]
        self.assertEqual(self.run_sim(on_time, ev).run()["violations"]["S2"], 0)
        self.assertEqual(self.run_sim(late, ev).run()["violations"]["S2"], 1)

    def test_a_lift_back_in_service_during_fire_gets_its_own_time(self):
        def go(s, t, floors):
            if t < 20:
                return ["stay"]
            return ["down"] if floors[0] > 0 else ["open"]
        ev = [("service", 5, 0, False), ("mode", 10, "fire"), ("service", 20, 0, True), ("mode", 90, "normal")]
        self.assertEqual(self.run_sim(go, ev).run()["violations"]["S2"], 0)

    def test_idle_fire_is_still_checked(self):
        # No passengers and fire mode still on at the end must not end the run early.
        r = self.run_sim(lambda s, t, floors: ["stay"], [("mode", 0, "fire")]).run()
        self.assertGreater(r["violations"]["S2"], 0)

    def test_riders_are_evacuated_and_not_scored(self):
        s = self.run_sim(lambda s, t, floors: ["down"] if floors[0] > 0 else ["open"],
                         [("onboard", 0, 0, 20), ("mode", 0, "fire"), ("mode", 50, "normal")], start=(2,))
        r = s.run()
        self.assertEqual(sum(r["violations"].values()), 0)
        self.assertTrue(s.people[0].evacuated)
        self.assertEqual(r["delivered"], 0)

    def test_replayed_call_errors_are_recorded(self):
        import sim

        class D:
            def __init__(self, f, n):
                self.fire = False
            def on_call(self, t, fl, d):
                if t >= 5:
                    raise ValueError("boom")
            def on_car_request(self, *a): pass
            def set_mode(self, t, m): pass
            def set_lift_available(self, *a): pass
            def step(self, t, floors): return ["stay"]
        ev = [("call", 0, 9, 1), ("mode", 2, "fire"), ("mode", 6, "normal")]
        self.assertGreater(sim.Simulation(D, self.scenario(ev, ticks=20)).run()["violations"]["C1"], 0)

    def test_the_v4_scripts_mix_fire_and_maintenance(self):
        kinds = {e[0] for e in scenarios.version("v4", 11)["events"]}
        self.assertLessEqual({"service", "mode"}, kinds)


if __name__ == "__main__":
    unittest.main()
