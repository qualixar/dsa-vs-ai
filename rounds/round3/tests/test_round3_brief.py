"""The brief states what the referee checks, names no vendor, and a known solution can meet it."""
import json
import os
import re
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
import baselines  # noqa: E402
import calibrate_round3 as K  # noqa: E402
import envelope_probes as E  # noqa: E402
import scenarios_v3 as G  # noqa: E402
import sim  # noqa: E402
import witness  # noqa: E402
import check_referee  # noqa: E402

BRIEF_DIR = os.path.join(ROOT, "brief-v3")
FILES = ["BRIEF.md", "CHANGE-v2.md", "CHANGE-v3.md", "CHANGE-v4.md", "CHANGE-v5.md"]


def text(name):
    with open(os.path.join(BRIEF_DIR, name)) as f:
        return f.read()


class Wording(unittest.TestCase):
    def test_limits_in_the_brief_are_the_referee_limits(self):
        limits = G.current_limits()
        self.assertIn(f"Time limit: {limits['everyone']['v1']} s", text("BRIEF.md"))
        self.assertIn(f"Time limit: {limits['everyone']['v2']} s", text("CHANGE-v2.md"))
        self.assertIn(f"Time limit: {limits['everyone']['v3']} s", text("CHANGE-v3.md"))
        self.assertIn(f"evacuated: {limits['everyone']['v4']} s", " ".join(text("CHANGE-v4.md").split()))
        v5 = text("CHANGE-v5.md")
        self.assertIn(f"at or below {limits['lobby_p95']} s", v5)
        self.assertIn(f"within {limits['upper']} s", v5)
        self.assertIn(f"Everyone arrives within {limits['everyone']['v5']} s", v5)

    def test_envelope_numbers_in_the_brief_are_the_generator_envelope(self):
        for name, env in (("BRIEF.md", G.ENVELOPE["v1"]), ("CHANGE-v2.md", G.ENVELOPE["v2"])):
            words = " ".join(text(name).split())
            self.assertIn(f"exactly {env['calls']} calls", words, name)
            self.assertIn(f"largest crowd is {env['crowd']} people", words, name)
            (w10, n10), (w60, n60), (w300, n300) = env["windows"]
            self.assertIn(f"{n10} calls in any 10 seconds, {n60} in any 60 seconds", words, name)
            self.assertIn(f"{n300} in any 5 minutes", words, name)
        v5 = " ".join(text("CHANGE-v5.md").split())
        env = G.ENVELOPE["v5"]
        self.assertIn("exactly 300 calls", v5)
        self.assertIn(f"{env['lobby']} go from floor 0", v5)
        self.assertIn(f"{env['upper']} start on floors 1 to 29", v5)
        self.assertIn(f"largest crowd is {env['crowd']} people", v5)
        self.assertIn(f"{env['windows'][0][1]} calls in any 10 seconds and {env['windows'][1][1]} in any 60 seconds", v5)
        self.assertIn(f"no more than {env['upper_windows'][0][1]} of the upstairs calls in any 60 seconds", v5)

    def test_acceptance_is_stated_as_sampled_days_with_no_universal_claim(self):
        words = " ".join(text("BRIEF.md").split())
        self.assertIn("Acceptance is measured on days drawn at random from inside the envelope", words)
        self.assertIn("Nobody claims that every day you could write down inside an envelope can meet its limit", words)


class Calibration(unittest.TestCase):
    def test_the_table_follows_the_rule_by_hand(self):
        reference = {f: {"worst_passenger": 100, "lobby_p95": 0, "upstairs": 0} for f in K.FAMILIES}
        reference["v5"] = {"worst_passenger": 1421, "lobby_p95": 1349, "upstairs": 139}
        probes = {f: {"everyone": [0, ""], "lobby_p95": [0, ""], "upper": [0, ""]} for f in K.FAMILIES}
        probes["v3"]["everyone"] = [507, "x"]
        t = K.table(reference, probes)
        self.assertEqual(t["everyone"], {"v1": 130, "v2": 130, "v3": 510, "v4": 130, "v5": 1850})
        self.assertEqual(t["lobby_p95"], 1760)
        self.assertEqual(t["upper"], 190)

    def test_ceil10(self):
        self.assertEqual([K.ceil10(x) for x in (130.0, 130.1, 180.7, 1847.3, 1.3 * 100)], [130, 140, 190, 1850, 130])

    def test_the_recorded_calibration_is_current(self):
        with open(K.OUT) as f:
            data = json.load(f)
        self.assertEqual(data["limits"], G.current_limits())
        with open(check_referee.COMMENT_CHANGE) as f:
            changes = json.load(f)["files"]
        for name, digest in data["file_sha256"].items():
            with open(os.path.join(ROOT, name), "rb") as f:
                self.assertIn(check_referee.status(f.read(), digest, changes.get(name)), ("match   ", "comment "), name)

    def test_a_tampered_referee_file_is_reported(self):
        with open(check_referee.COMMENT_CHANGE) as f:
            change = json.load(f)["files"]["scenarios_v3.py"]
        with open(os.path.join(ROOT, "scenarios_v3.py"), "rb") as f:
            raw = f.read()
        self.assertEqual(check_referee.status(raw, change["certified_sha256"], change), "comment ")
        self.assertEqual(check_referee.status(raw + b"x = 1\n", change["certified_sha256"], change), "DIFFERS ")


def strict(policy, family, seed):
    return sim.Simulation(policy, G.scenario(family, seed)).run()


class Feasible(unittest.TestCase):
    def test_reference_breaks_nothing_on_fresh_days_in_any_family(self):
        for fam in K.FAMILIES:
            for seed in range(900000, 900060):
                self.assertEqual(sum(strict(baselines.Baseline, fam, seed)["violations"].values()), 0, (fam, seed))

    def test_witness_breaks_nothing_on_fresh_days_in_any_family(self):
        for fam in K.FAMILIES:
            for seed in range(900000, 900060):
                self.assertEqual(sum(strict(witness.Sweep, fam, seed)["violations"].values()), 0, (fam, seed))

    def test_hand_built_days_are_permitted_and_the_witness_meets_every_limit(self):
        limits = G.current_limits()
        for fam in K.FAMILIES:
            w = E.worst(fam)
            self.assertEqual((w["safety"], w["undelivered"]), (0, 0), fam)
            self.assertLessEqual(w["everyone"][0], limits["everyone"][fam], fam)
        v5 = E.worst("v5")
        self.assertLessEqual(v5["lobby_p95"][0], limits["lobby_p95"])
        self.assertLessEqual(v5["upper"][0], limits["upper"])

    def test_the_audit_shuttle_probe_cannot_be_written_inside_the_envelope(self):
        for rate, seconds in ((4, 10), (2, 20)):
            ev = [("call", i // rate, 0, 29) for i in range(40)]
            self.assertTrue(G.validate_schedule("v1", ev), (rate, seconds))
        # the same shuttle packed as early as the envelope allows, with the lift starting at the far end
        ev = E._earliest("v1", lambda i: (0, 29))
        self.assertEqual(G.validate_schedule("v1", ev), [])
        r = E.run_day(witness.Sweep, "v1", "shuttle", ev, [29])
        self.assertEqual(r["violations"]["L1"], 0)
        self.assertLessEqual(r["max_time"], G.LIMITS["v1"])


class LobbyFirst(baselines.Baseline):
    """The manager's sentence read literally: upstairs calls wait until nothing is waiting at floor 0."""
    def _targets(self, i):
        t = super()._targets(i)
        if 0 in self.hall or any(0 in self.car[j] for j in range(self.n)):
            return self.car[i] | ({0} if self.hall.get(0) == i else set())
        return t


class Nuance(unittest.TestCase):
    def test_the_literal_reading_fails_the_upstairs_measure_on_every_day_tried(self):
        for seed in range(910000, 910020):
            self.assertEqual(strict(LobbyFirst, "v5", seed)["violations"]["T5c"], 1, seed)


if __name__ == "__main__":
    unittest.main()
