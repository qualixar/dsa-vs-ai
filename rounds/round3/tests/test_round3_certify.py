"""referee_certify.py on small numbers: everything it promises is in the certificate, and it refuses when it should."""
import json
import os
import pathlib
import sys
import tempfile
import unittest
from unittest import mock

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
import referee_certify as R  # noqa: E402
import scenarios_v3 as G  # noqa: E402

SMALL = dict(random_days=4, candidates=6, hardest=2, min_keep=4, fresh_mutants=3, existing_bugs=0)
H, S = "a" * 64, "b" * 64


class Certify(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dir = tempfile.TemporaryDirectory(prefix="r3-cert-")
        cls.out = os.path.join(cls.dir.name, "cert.json")
        cls.code = R.certify(H, S, cls.out, workers=6, **SMALL)
        cls.cert = json.loads(pathlib.Path(cls.out).read_text())

    @classmethod
    def tearDownClass(cls):
        cls.dir.cleanup()

    def test_it_succeeds_and_binds_the_files_and_inputs(self):
        self.assertEqual(self.code, 0)
        self.assertEqual(self.cert["sealed_hash"], H)
        self.assertEqual(self.cert["salt"], S)
        for name in ("scenarios_v3.py", "sim.py", "judge.py", "team_host.py", "baselines.py", "referee_certify.py"):
            self.assertEqual(self.cert["file_sha256"][name], R.sha(os.path.join(ROOT, name)))
        self.assertEqual(self.cert["limits"], G.current_limits())

    def test_days_per_family_are_counted(self):
        for fam, entry in self.cert["families"].items():
            self.assertEqual(entry["generated"], 10)
            self.assertEqual(entry["kept"], len(entry["kept_seeds"]))
            self.assertEqual(entry["kept"] + entry["dropped_on_margin"] + entry["not_chosen"], 10)
            self.assertGreaterEqual(entry["kept"], 4)
            self.assertLessEqual(entry["reference_worst"], G.LIMITS[fam] / 1.15)

    def test_broken_dispatcher_catch_rate_is_measured_and_stated(self):
        broken = self.cert["broken_dispatchers"]
        self.assertEqual(broken["planted"], 5)
        self.assertEqual(broken["caught"], sum(r["caught"] for r in broken["rows"].values()))
        for name, rule in R.BROKEN.items():
            self.assertEqual(broken["rows"][name]["expected_rule"], rule)

    def test_mutant_catch_rate_is_measured_and_stated(self):
        for key, n in (("fresh", 3), ("existing", 0)):
            block = self.cert["mutants"][key]
            self.assertEqual(block["planted"], n, key)
            self.assertEqual(len(block["rows"]), n)
            self.assertEqual(block["changed_a_trace"], sum(r["changed_trace"] for r in block["rows"]))
            self.assertEqual(block["broke_a_rule"], sum(r["broke_rule"] for r in block["rows"]))
            self.assertEqual(block["only_shifted_quality"], sum(r["changed_trace"] and not r["broke_rule"] for r in block["rows"]))
            self.assertIn("catch_rate", block)

    def test_the_climax_day_is_named_and_has_a_returning_lift_if_any_day_does(self):
        name = self.cert["climax_day"]
        if name is not None:
            self.assertIn(int(name.split("-")[1]), self.cert["families"]["v4"]["kept_seeds"])

    def test_certified_set_reads_back_the_same_days(self):
        days, batches = G.certified_set(self.out)
        self.assertEqual(sorted(days), ["v1", "v2", "v3", "v4", "v5"])
        self.assertEqual(len(batches), 20)
        self.assertEqual(len(days["v3"]), self.cert["families"]["v3"]["kept"])

class Refusals(unittest.TestCase):
    def test_refuses_when_a_family_keeps_too_few_days(self):
        with tempfile.TemporaryDirectory() as d:
            out = os.path.join(d, "c.json")
            self.assertNotEqual(R.certify(H, S, out, workers=2, **{**SMALL, "min_keep": 9}), 0)
            self.assertFalse(os.path.exists(out))

    def test_refuses_when_a_broken_dispatcher_passes(self):
        planted = {**R.BROKEN, "Baseline": "S2"}   # the clean reference can't fail anything
        with tempfile.TemporaryDirectory() as d, mock.patch.object(R, "BROKEN", planted):
            out = os.path.join(d, "c.json")
            self.assertNotEqual(R.certify(H, S, out, workers=6, **{**SMALL, "fresh_mutants": 0, "existing_bugs": 0}), 0)
            self.assertFalse(os.path.exists(out))


if __name__ == "__main__":
    unittest.main()
