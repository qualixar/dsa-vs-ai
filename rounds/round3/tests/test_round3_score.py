"""Every outcome of the scoring rule, written out. The rule is in the README, under round 3."""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import score_round3 as S  # noqa: E402





class Table(unittest.TestCase):
    """(arm A's versions in two runs, arm B's versions in two runs) -> winner"""
    CASES = [
        # a = 2: AI, whatever arm B did
        ([5, 5], [5, 5], "AI"), ([5, 5], [0, 0], "AI"), ([5, 5], [5, 0], "AI"), ([5, 5], [4, 4], "AI"),
        # a = 1
        ([5, 4], [5, 5], "DSA"),     # b=2 > a=1, 10 > 9
        ([5, 0], [5, 5], "DSA"),
        ([5, 4], [5, 4], "nobody"),  # b=1, not more clean runs
        ([5, 4], [5, 0], "nobody"),
        ([5, 4], [4, 4], "nobody"),  # b=0
        ([5, 0], [4, 4], "nobody"),  # b=0 though more versions
        # a = 0
        ([4, 4], [5, 5], "DSA"),     # b=2 > 0, 10 > 8
        ([4, 3], [5, 3], "DSA"),     # b=1 > 0, 8 > 7
        ([4, 4], [5, 0], "nobody"),  # the audit's case: b=1 > 0 but 5 < 8 versions
        ([4, 4], [5, 3], "nobody"),  # b=1 > 0 but 8 = 8: must be strictly greater
        ([4, 3], [4, 4], "nobody"),  # more versions but no clean run
        ([0, 0], [0, 0], "nobody"),
        ([3, 2], [4, 4], "nobody"),
    ]

    def test_every_case(self):
        for alone, notes, winner in self.CASES:
            d = S.decide(alone, notes)
            self.assertEqual(d["winner"], winner, (alone, notes, d))

    def test_scores_follow_the_winner(self):
        self.assertEqual(S.decide([5, 5], [5, 5])["final_score"], {"AI": 3, "DSA": 0})
        self.assertEqual(S.decide([4, 4], [5, 5])["final_score"], {"AI": 2, "DSA": 1})
        nobody = S.decide([4, 4], [4, 4])
        self.assertEqual(nobody["final_score"], {"AI": 2, "DSA": 0})
        self.assertIn("nobody", nobody["sentence"].lower())

    def test_counts_are_always_reported(self):
        d = S.decide([5, 3], [5, 5])
        self.assertEqual(d["clean"], {"alone": 1, "notes": 2})
        self.assertEqual(d["versions_passed"], {"alone": [5, 3], "notes": [5, 5]})
        self.assertEqual(d["versions_total"], {"alone": 8, "notes": 10})

    def test_exhaustive_rule_agrees_with_the_written_rule(self):
        counts = range(0, 6)
        seen = set()
        for a1 in counts:
            for a2 in counts:
                for b1 in counts:
                    for b2 in counts:
                        d = S.decide([a1, a2], [b1, b2])
                        a = (a1 == 5) + (a2 == 5)
                        b = (b1 == 5) + (b2 == 5)
                        want = "AI" if a == 2 else "DSA" if b > a and b1 + b2 > a1 + a2 else "nobody"
                        self.assertEqual(d["winner"], want, (a1, a2, b1, b2))
                        seen.add(want)
        self.assertEqual(seen, {"AI", "DSA", "nobody"})

    def test_a_missing_valid_run_is_inconclusive_and_scores_nobody(self):
        for alone, notes in (([5], [5, 5]), ([5, 5], [5]), ([], [])):
            d = S.decide(alone, notes)
            self.assertEqual(d["winner"], "inconclusive", (alone, notes))
            self.assertEqual(d["final_score"], {"AI": 2, "DSA": 0})

    def test_no_causal_claim_in_any_sentence(self):
        for alone, notes, _ in self.CASES:
            sentence = S.decide(alone, notes)["sentence"].lower()
            self.assertIn("four-run case study", sentence)
            for word in ("because of", "caused", "proves", "makes the difference", "made the difference"):
                self.assertNotIn(word, sentence)


class Practice(unittest.TestCase):
    """The re-examination table, on the reference: counts are separate, the status says unscored."""

    def test_denominators_are_separate_and_it_is_never_a_verdict(self):
        import json
        import pathlib
        import tempfile
        import referee_certify as RC
        with tempfile.TemporaryDirectory() as d:
            cert = pathlib.Path(d, "cert.json")
            cert.write_text(json.dumps({"families": {f: {"kept_seeds": [1000, 1001, 1002]} for f in S.FAMILIES}}))
            repo = pathlib.Path(d, "repo")
            (repo / "dispatcher").mkdir(parents=True)
            (repo / "dispatcher/__init__.py").write_text(RC.reference_source())
            out = pathlib.Path(d, "practice.json")
            with open(os.devnull, "w") as sink, __import__("contextlib").redirect_stdout(sink):
                self.assertEqual(S.main(["--practice", str(repo), "--certificate", str(cert), "--out", str(out), "--workers", "4"]), 0)
            report = json.loads(out.read_text())
        self.assertIn("unscored", report["status"])
        for fam, row in report["old_brief_limits"].items():
            self.assertEqual(row["generated"], 3, fam)
            self.assertEqual(row["generated"], row["excluded_reference_fails_old_limit"] + row["evaluated"], fam)
            for rule, passing in row["days_passing_per_rule"].items():
                self.assertLessEqual(passing, row["evaluated"], (fam, rule))
        self.assertIn("passes_round_three_limits", report["information_only_round_three_limits"]["v3"])


if __name__ == "__main__":
    unittest.main()
