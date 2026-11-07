"""Act 3 simulator self-tests: the baseline is clean, every check fires on the
bug it exists for, and the quality optimum is exact."""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import baselines  # noqa: E402
import scenarios  # noqa: E402
import sim  # noqa: E402


def run(cls, sc):
    return sim.Simulation(cls, sc).run()


class Act3(unittest.TestCase):
    def test_the_brief_states_the_traffic_the_scenarios_use(self):
        with open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "BRIEF.md")) as f:
            brief = f.read()
        calls = {v: sum(e[0] == "call" for e in scenarios.version(v, 1)["events"]) for v in ("v1", "v2", "v3", "v4", "v5")}
        self.assertEqual(calls, {"v1": 40, "v2": 120, "v3": 120, "v4": 120, "v5": 300})
        self.assertIn("40 calls spread over 10 minutes for v1, 120 calls spread over 10 minutes for v2 to v4", brief)

    def test_baseline_is_clean_on_every_version(self):
        for sc in scenarios.all_versions():
            v = run(baselines.Baseline, sc)["violations"]
            self.assertEqual(sum(v.values()), 0, (sc["name"], v))

    def test_runs_are_deterministic(self):
        sc = scenarios.version("v3", 11)
        self.assertEqual(run(baselines.Baseline, sc), run(baselines.Baseline, sc))

    def test_quality_optimum_is_exact(self):
        for sc in scenarios.q1_batches():
            opt = sim.optimum_onboard(sc["q1"]["start"], sc["q1"]["dests"])
            self.assertEqual(run(baselines.OptimalOnboard, sc)["total_time"], opt, sc["name"])
            self.assertGreaterEqual(run(baselines.Baseline, sc)["total_time"], opt)

    def test_quality_check_separates_good_from_mediocre(self):
        gaps = []
        for sc in scenarios.q1_batches():
            opt = sim.optimum_onboard(sc["q1"]["start"], sc["q1"]["dests"])
            gaps.append(run(baselines.Baseline, sc)["total_time"] / opt - 1)
        self.assertGreater(max(gaps), 0.2)

    def test_fire_check(self):
        v = run(baselines.IgnoresFire, scenarios.version("v4", 11))["violations"]
        self.assertGreater(v["S2"], 0)

    def test_out_of_service_check(self):
        v = run(baselines.MovesWhileOutOfService, scenarios.version("v3", 11))["violations"]
        self.assertGreater(v["S3"], 0)

    def test_contract_check(self):
        v = run(baselines.WrongCommandCount, scenarios.version("v2", 11))["violations"]
        self.assertGreater(v["C1"], 0)

    def test_shaft_bounds_check(self):
        sc = {"name": "idle-at-0", "floors": 10, "lifts": 1, "start_floors": [0], "max_ticks": 60,
              "bound": None, "events": [("call", 5, 3, 7)]}
        v = run(baselines.FallsThroughFloor, sc)["violations"]
        self.assertGreater(v["S1"], 0)

    def test_liveness_check(self):
        v = run(baselines.OnlyCarCalls, scenarios.version("v1", 11))["violations"]
        self.assertGreater(v["L1"], 0)

    def test_crashing_dispatcher_is_a_contract_violation_not_a_crash(self):
        class Crashes(baselines.Baseline):
            def step(self, t, floors_now):
                raise RuntimeError("boom")
        v = run(Crashes, scenarios.version("v1", 11))["violations"]
        self.assertGreater(v["C1"], 0)

    def test_left_behind_passengers_call_again(self):
        sc = {"name": "full", "floors": 10, "lifts": 1, "start_floors": [0], "max_ticks": 500,
              "bound": None, "events": [("call", 0, 0, 5)] * 15}
        r = run(baselines.Baseline, sc)
        self.assertEqual(r["delivered"], 15)


if __name__ == "__main__":
    unittest.main()
