"""Self-tests: the harness must pass good code and catch each kind of bad code
at the right gate. Run: python3 -I -m unittest discover -s tests -v (from harness/)."""
import os
import random
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
import grade  # noqa: E402

RAIN = grade.load_spec("rain")
ELEV = grade.load_spec("elevator")


def fixture(problem, name):
    return os.path.join(HERE, "fixtures", problem, name + ".py")


class References(unittest.TestCase):
    def test_references_match_leetcode_examples(self):
        for spec in (RAIN, ELEV):
            for args, want in spec.examples():
                self.assertEqual(spec.reference(*args), want)
                self.assertEqual(spec.fast(*args), want)

    def test_fast_equals_reference_on_random_cases(self):
        for spec in (RAIN, ELEV):
            for args in spec.edge_cases() + spec.random_cases(count=2000, seed=7):
                self.assertEqual(spec.fast(*args), spec.reference(*args), args)

    def test_fast_equals_reference_with_eight_requests(self):
        import random as _r
        rng = _r.Random(5)
        for _ in range(15):
            n = rng.choice([20, 1000])
            args = [n, rng.randrange(n), rng.sample(range(n), 8)]
            self.assertEqual(ELEV.fast(*args), ELEV.reference(*args), args)

    def test_nearest_first_trap_is_real(self):
        args = [20, 10, [8, 13, 14, 15, 16, 17]]
        self.assertEqual(ELEV.reference(*args), 41)
        self.assertEqual(ELEV.nearest_first(*args), 47)

    def test_nearest_first_loses_often_on_random_cases(self):
        cases = ELEV.random_cases(count=1000, seed=11)
        losses = sum(ELEV.nearest_first(*a) != ELEV.reference(*a) for a in cases)
        self.assertGreater(losses, 0)

    def test_sanity_rules_accept_correct_answers(self):
        rng = random.Random(3)
        for spec in (RAIN, ELEV):
            for args in rng.sample(spec.random_cases(), 300):
                self.assertIsNone(spec.sanity(args, spec.reference(*args)), args)


class Grader(unittest.TestCase):
    def grade(self, spec, problem, name):
        return grade.grade_one(spec, fixture(problem, name))

    def test_good_rain_survives(self):
        self.assertTrue(self.grade(RAIN, "rain", "good_two_pointer")["survived"])

    def test_good_elevator_survives(self):
        self.assertTrue(self.grade(ELEV, "elevator", "good_dp")["survived"])

    def test_quadratic_rain_fails_only_at_scale(self):
        rec = self.grade(RAIN, "rain", "slow_quadratic")
        self.assertTrue(rec["gates"]["examples"]["pass"])
        self.assertTrue(rec["gates"]["correctness"]["pass"])
        self.assertEqual(rec["first_fail"], "scale")

    def test_off_by_one_rain_fails_correctness(self):
        rec = self.grade(RAIN, "rain", "wrong_off_by_one")
        self.assertIn(rec["first_fail"], ("examples", "correctness"))

    def test_nearest_first_elevator_passes_examples_then_fails(self):
        rec = self.grade(ELEV, "elevator", "nearest_first")
        self.assertTrue(rec["gates"]["examples"]["pass"])
        self.assertEqual(rec["first_fail"], "correctness")

    def test_brute_force_elevator_fails_on_medium_sizes(self):
        rec = self.grade(ELEV, "elevator", "simulates_floors")
        self.assertTrue(rec["gates"]["examples"]["pass"])
        self.assertEqual(rec["first_fail"], "correctness")

    def test_wrong_only_on_medium_sizes_is_caught(self):
        rec = self.grade(ELEV, "elevator", "medium_wrong")
        self.assertEqual(rec["first_fail"], "correctness")

    def test_recursive_solution_is_not_failed_by_settings(self):
        self.assertTrue(self.grade(ELEV, "elevator", "recursive_dp")["survived"])

    def test_prints_to_raw_stdout_do_not_corrupt_results(self):
        self.assertTrue(self.grade(RAIN, "rain", "prints_to_fd")["survived"])

    def test_leetcode_style_annotations_work_without_imports(self):
        self.assertTrue(self.grade(RAIN, "rain", "list_annotation")["survived"])

    def test_float_answer_counts_as_wrong_with_reason(self):
        rec = self.grade(RAIN, "rain", "returns_float")
        self.assertEqual(rec["first_fail"], "examples")
        self.assertIn("<float>", str(rec["gates"]["examples"]["fail"]["got"]))

    def test_hard_exit_is_a_failure_not_a_crash(self):
        rec = self.grade(RAIN, "rain", "exits_early")
        self.assertEqual(rec["first_fail"], "examples")

    def test_private_folders_are_unreadable(self):
        self.assertTrue(self.grade(RAIN, "rain", "reads_private_files")["survived"])

    def test_writes_outside_workdir_are_blocked(self):
        target = os.path.expanduser("~/grade-escape-test.txt")
        rec = self.grade(RAIN, "rain", "writes_outside")
        self.assertTrue(rec["survived"])
        self.assertFalse(os.path.exists(target))

    def test_patching_the_clock_does_not_beat_the_timer(self):
        rec = self.grade(RAIN, "rain", "patches_clock")
        self.assertEqual(rec["first_fail"], "scale")
        self.assertIn("perf_counter", rec["flags"])

    def test_infinite_loop_is_stopped(self):
        rec = self.grade(RAIN, "rain", "infinite_loop")
        self.assertEqual(rec["first_fail"], "examples")
        self.assertIn("timeout", rec["gates"]["examples"]["fail"]["error"])

    def test_syntax_error_is_reported(self):
        rec = self.grade(RAIN, "rain", "syntax_error")
        self.assertEqual(rec["first_fail"], "examples")
        self.assertIn("SyntaxError", rec["gates"]["examples"]["fail"]["error"])

    def test_network_is_blocked(self):
        rec = self.grade(RAIN, "rain", "tries_network")
        self.assertFalse(rec["gates"]["examples"]["pass"])
        self.assertIn("Error", str(rec["gates"]["examples"]["fail"]["got"]))


if __name__ == "__main__":
    unittest.main()
