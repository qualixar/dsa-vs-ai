"""Simulator additions for round three: the rush measures, completion reasons and the conservation check."""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import baselines  # noqa: E402
import scenarios  # noqa: E402
import scenarios_v3 as G  # noqa: E402
import sim  # noqa: E402


def day(events, lifts=1, floors=10, start=None, **extra):
    return {"name": "t", "floors": floors, "lifts": lifts, "start_floors": start or [0] * lifts, "max_ticks": 500,
            "bound": None, "events": events, **extra}


class Holds(baselines.Baseline):
    def _command(self, i):
        return "stay"


class RushMeasures(unittest.TestCase):
    def test_keys_appear_only_when_the_day_sets_them(self):
        legacy = sim.Simulation(baselines.Baseline, scenarios.version("v5", 11)).run()
        self.assertNotIn("T5b", legacy["violations"])
        self.assertNotIn("T5c", legacy["violations"])
        rush = sim.Simulation(baselines.Baseline, G.scenario("v5", 1)).run()
        self.assertIn("T5b", rush["violations"])
        self.assertIn("T5c", rush["violations"])
        self.assertEqual(rush["violations"]["T5"], 0)

    def test_lobby_and_upstairs_numbers_are_measured_from_the_riders(self):
        ev = [("call", 0, 0, 3), ("call", 0, 0, 5), ("call", 0, 8, 9)]
        s = sim.Simulation(baselines.Baseline, day(ev, lobby_p95_target=1, rush_upper_limit=1))
        r = s.run()
        lobby = sorted(p.t_done - p.t_call for p in s.people if p.origin0 == 0)
        upper = [p.t_done - p.t_call for p in s.people if p.origin0 != 0]
        self.assertEqual(r["lobby_p95"], lobby[-1])
        self.assertEqual(r["rush_upper_max"], max(upper))
        self.assertEqual(r["violations"]["T5b"], 1)
        self.assertEqual(r["violations"]["T5c"], 1)

    def test_an_upstairs_rider_never_delivered_counts_against_the_upstairs_limit(self):
        r = sim.Simulation(Holds, day([("call", 0, 8, 9)], rush_upper_limit=300)).run()
        self.assertEqual(r["violations"]["T5c"], 1)


class Completions(unittest.TestCase):
    def test_a_rider_unloaded_at_their_floor_by_maintenance_is_legal(self):
        sc = day([("onboard", 0, 0, 0), ("service", 1, 0, False)], lifts=2, start=[0, 5])
        s = sim.Simulation(Holds, sc)
        r = s.run()
        self.assertEqual(s.people[0].reason, "maintenance")
        self.assertEqual(r["delivered"], 1)
        self.assertEqual(r["completions"]["maintenance"], 1)

    def test_normal_and_evacuated_reasons_are_recorded(self):
        ev = [("call", 0, 0, 3), ("call", 0, 0, 9), ("mode", 5, "fire"), ("mode", 40, "normal")]
        s = sim.Simulation(baselines.Baseline, day(ev))
        r = s.run()
        self.assertEqual(s.people[0].reason, "normal")
        self.assertEqual(s.people[1].reason, "evacuated")
        self.assertTrue(s.people[1].evacuated)
        self.assertEqual(r["completions"], {"normal": 1, "maintenance": 0, "evacuated": 1})

    def test_each_reason_rejects_an_illegal_transition(self):
        sc = day([("call", 0, 0, 3)], lifts=2)
        cases = [("normal", dict(floor=2, available=True, mode="normal")),   # not at their floor
                 ("normal", dict(floor=3, available=False, mode="normal")),  # lift is out of service
                 ("normal", dict(floor=3, available=True, mode="fire")),     # fire: nobody arrives normally
                 ("maintenance", dict(floor=2, available=False, mode="normal")),  # wrong floor
                 ("maintenance", dict(floor=3, available=True, mode="normal")),   # lift is in service
                 ("evacuated", dict(floor=0, available=True, mode="normal")),     # no fire
                 ("evacuated", dict(floor=2, available=True, mode="fire")),       # not the ground floor
                 ("nonsense", dict(floor=3, available=True, mode="normal"))]
        for reason, state in cases:
            s = sim.Simulation(baselines.Baseline, sc)
            lift = s.lifts[0]
            lift.floor, lift.available = state["floor"], state["available"]
            s.mode = state["mode"]
            p = sim.Passenger(0, 0, 3, 0)
            with self.assertRaises(sim.SimulatorError, msg=(reason, state)):
                s._finish(p, 1, reason, lift)


class Conservation(unittest.TestCase):
    def test_a_passenger_lost_by_the_simulator_voids_the_run(self):
        class LosesRiders(sim.Simulation):
            def _open(self, t, i, lift):
                super()._open(t, i, lift)
                if t > 5 and lift.riders:
                    lift.riders.pop()
        with self.assertRaises(sim.SimulatorError):
            LosesRiders(baselines.Baseline, G.scenario("v1", 1)).run()

    def test_a_passenger_in_two_places_voids_the_run(self):
        class Doubles(sim.Simulation):
            def _open(self, t, i, lift):
                super()._open(t, i, lift)
                if lift.riders:
                    self.waiting.setdefault(lift.floor, []).append(lift.riders[0])
        with self.assertRaises(sim.SimulatorError):
            Doubles(baselines.Baseline, G.scenario("v1", 1)).run()

    def test_it_is_not_swallowed_as_a_team_error(self):
        self.assertFalse(issubclass(sim.SimulatorError, Exception))

    def test_reference_runs_clean_on_every_family(self):
        for fam in ("v1", "v2", "v3", "v4", "v5"):
            r = sim.Simulation(baselines.Baseline, G.scenario(fam, 2)).run()
            self.assertEqual(sum(r["completions"].values()), r["passengers"], fam)


if __name__ == "__main__":
    unittest.main()
