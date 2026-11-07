"""Round three generator: every finished day obeys the stated envelope. Includes the old gencheck self-test."""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import scenarios_v3 as G  # noqa: E402

FAMILIES = ("v1", "v2", "v3", "v4", "v5")


def calls(sc):
    return [e for e in sc["events"] if e[0] == "call"]


def overlap(events):
    """Seconds with two lifts out, measured from the finished schedule, independent of the validator."""
    state, last, total = [True] * 3, 0, 0
    for e in sorted((e for e in events if e[0] == "service"), key=lambda e: e[1]):
        if state.count(False) >= 2:
            total += e[1] - last
        state[e[2]], last = e[3], e[1]
    if state.count(False) >= 2:
        total = float("inf")
    return total


class Counts(unittest.TestCase):
    def test_passenger_totals_are_exact_on_every_day(self):
        want = {"v1": 40, "v2": 120, "v3": 120, "v4": 120, "v5": 300}
        for fam in FAMILIES:
            for seed in range(300):
                self.assertEqual(len(calls(G.scenario(fam, seed))), want[fam], (fam, seed))

    def test_v5_counts_and_origins_are_exact(self):
        for seed in range(300):
            c = calls(G.scenario("v5", seed))
            lobby = [e for e in c if e[2] == 0]
            upper = [e for e in c if e[2] != 0]
            self.assertEqual(len(lobby), 240, seed)
            self.assertEqual(len(upper), 60, seed)
            self.assertTrue(all(1 <= e[2] <= 29 for e in upper))
            self.assertTrue(all(1 <= e[3] <= 29 for e in lobby))
            self.assertTrue(all(0 <= e[1] < 300 for e in c))

    def test_no_rider_travels_to_their_own_floor(self):
        for fam in FAMILIES:
            for seed in range(100):
                self.assertTrue(all(e[2] != e[3] for e in calls(G.scenario(fam, seed))))

    def test_v5_has_no_outage_or_fire(self):
        for seed in range(100):
            self.assertTrue(all(e[0] == "call" for e in G.scenario("v5", seed)["events"]))


class CrowdsAndBursts(unittest.TestCase):
    def test_crowds_and_bursts_appear_within_the_totals(self):
        crowd_v1 = crowd_v2 = burst_v2 = 0
        for seed in range(400):
            tally = {}
            for e in calls(G.scenario("v1", seed)):
                tally[(e[1], e[2])] = tally.get((e[1], e[2]), 0) + 1
            crowd_v1 += max(tally.values()) >= 12
            tally = {}
            times = sorted(e[1] for e in calls(G.scenario("v2", seed)))
            for e in calls(G.scenario("v2", seed)):
                tally[(e[1], e[2])] = tally.get((e[1], e[2]), 0) + 1
            crowd_v2 += max(tally.values()) >= 15
            burst_v2 += G.busiest(times, 10) >= 30
        self.assertGreater(crowd_v1, 60)
        self.assertGreater(crowd_v2, 60)
        self.assertGreater(burst_v2, 60)


class FinishedScheduleSelfTest(unittest.TestCase):
    """The old gencheck.py, kept as a unit test, measured on finished schedules."""

    def test_maintenance_conditions_hold_on_every_finished_day(self):
        for seed in range(2000):
            for fam in ("v3", "v4"):
                ev = G.scenario(fam, seed)["events"]
                self.assertLessEqual(overlap(ev), G.TWO_OUT_MAX_S, (fam, seed))
                avail = [True] * 3
                taken = {}
                for e in sorted((e for e in ev if e[0] == "service"), key=lambda e: e[1]):
                    avail[e[2]] = e[3]
                    self.assertTrue(any(avail), (fam, seed))
                    if not e[3]:
                        taken[e[2]] = taken.get(e[2], 0) + 1
                self.assertLessEqual(len(taken), 2, (fam, seed))
                self.assertTrue(all(n == 1 for n in taken.values()), (fam, seed))

    def test_fire_conditions_and_returning_lifts(self):
        returning = 0
        for seed in range(2000):
            ev = G.scenario("v4", seed)["events"]
            modes = [e for e in ev if e[0] == "mode"]
            self.assertEqual([m[2] for m in modes], ["fire", "normal"])
            start, end = modes[0][1], modes[1][1]
            self.assertTrue(G.FIRE_START[0] <= start < G.FIRE_START[1], seed)
            self.assertTrue(G.FIRE_LENGTH[0] <= end - start <= G.FIRE_LENGTH[1], seed)
            out_at_start = set()
            for e in sorted((e for e in ev if e[0] == "service"), key=lambda e: e[1]):
                if e[1] <= start:
                    out_at_start = (out_at_start - {e[2]}) if e[3] else (out_at_start | {e[2]})
            back = any(e[0] == "service" and e[3] and e[2] in out_at_start and start < e[1] < end for e in ev)
            returning += back
        self.assertGreater(returning, 500, "about two days in five should have a lift returning during the fire")

    def test_seed_15547_regression_from_the_audit(self):
        self.assertEqual(G.validate_schedule("v4", G.scenario("v4", 15547)["events"]), [])


class Validator(unittest.TestCase):
    def test_every_generated_day_passes_the_validator(self):
        for fam in FAMILIES:
            for seed in range(500):
                self.assertEqual(G.validate_schedule(fam, G.scenario(fam, seed)["events"]), [], (fam, seed))

    def test_audit_shuttle_day_is_outside_the_envelope(self):
        ev = [("call", i // 4, 0, 29) for i in range(40)]
        self.assertTrue(G.validate_schedule("v1", ev))

    def test_validator_rejects_each_broken_condition(self):
        base = G.scenario("v3", 3)["events"]
        keep = [e for e in base if e[0] == "call"]
        cases = {
            "extra call": keep + [("call", 5, 1, 2)],
            "own floor": [("call", 5, 1, 1)] + keep[1:],
            "all out": keep + [("service", 10, 0, False), ("service", 11, 1, False), ("service", 12, 2, False)],
            "long overlap": keep + [("service", 172, 0, False), ("service", 173, 1, False), ("service", 300, 0, True)],
            "same lift twice": keep + [("service", 10, 0, False), ("service", 20, 0, True), ("service", 30, 0, False)],
            "three lifts": keep + [("service", 10, 0, False), ("service", 20, 0, True), ("service", 30, 1, False),
                                   ("service", 40, 1, True), ("service", 50, 2, False)],
            "fire in v3": keep + [("mode", 100, "fire"), ("mode", 110, "normal")],
        }
        for name, ev in cases.items():
            self.assertTrue(G.validate_schedule("v3", ev), name)
        v4 = [e for e in G.scenario("v4", 3)["events"] if e[0] != "mode"]
        for name, modes in {"long fire": [("mode", 100, "fire"), ("mode", 221, "normal")],
                            "early fire": [("mode", 10, "fire"), ("mode", 30, "normal")],
                            "two fires": [("mode", 100, "fire"), ("mode", 120, "normal"), ("mode", 200, "fire"),
                                          ("mode", 220, "normal")]}.items():
            self.assertTrue(G.validate_schedule("v4", v4 + modes), name)

    def test_regeneration_is_deterministic(self):
        for fam in FAMILIES:
            self.assertEqual(G.scenario(fam, 77), G.scenario(fam, 77))
            self.assertNotEqual(G.scenario(fam, 77)["events"], G.scenario(fam, 78)["events"])


class Seeds(unittest.TestCase):
    def test_seeds_need_the_hash_and_the_salt(self):
        a = G.seeds("v1", "h" * 64, "s" * 64, 10)
        self.assertEqual(a, G.seeds("v1", "h" * 64, "s" * 64, 10))
        self.assertNotEqual(a, G.seeds("v1", "h" * 64, "t" * 64, 10))
        self.assertNotEqual(a, G.seeds("v1", "i" * 64, "s" * 64, 10))
        self.assertNotEqual(a, G.seeds("v2", "h" * 64, "s" * 64, 10))
        self.assertEqual(len(set(a)), 10)


if __name__ == "__main__":
    unittest.main()
