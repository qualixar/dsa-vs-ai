"""Tests for the runner: it must catch a wrong fast, a wrong answer that survives, a crash and a hang."""
import pathlib
import subprocess
import sys
import tempfile
import textwrap
import time
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT))
import check  # noqa: E402

CASES_PY = """
TITLE = "Largest"
FAMILY = "Arrays and hashing"
LEETCODE = None
MAX_SIZE = 6


def generate(rng, size):
    return ([rng.randint(-5, 5) for _ in range(size + 1)],)


def big(rng):
    return ([1] * 1000,)
"""
SLOW = "def solve(nums):\n    return sorted(nums)[-1]\n"
FAST = "def solve(nums):\n    return max(nums)\n"
WRONG = """
def gut(nums):
    return nums[0]


def planted(nums):
    return abs(max(nums))
"""


def make_case(root, name="largest", cases=CASES_PY, slow=SLOW, fast=FAST, wrong=WRONG):
    folder = pathlib.Path(root) / name
    folder.mkdir()
    for filename, text in (("cases.py", cases), ("slow.py", slow), ("fast.py", fast), ("wrong.py", wrong)):
        (folder / filename).write_text(textwrap.dedent(text))
    return folder


class RunCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)

    def run_it(self, **files):
        return check.run_case(make_case(self.tmp.name, **files), trials=300)

    def test_a_good_case_is_ok_and_reports_failures_of_both_wrong_answers(self):
        r = self.run_it()
        self.assertTrue(r["ok"], r["problems"])
        self.assertEqual(r["subjects"]["fast"]["fails"], 0)
        self.assertGreater(r["subjects"]["gut"]["fails"], 0)
        self.assertGreater(r["subjects"]["planted"]["fails"], 0)

    def test_smallest_failing_input_is_the_smallest(self):
        r = self.run_it()
        # abs(max(nums)) can only be wrong when every number is negative, so one number is enough.
        smallest = r["subjects"]["planted"]["smallest"]
        self.assertRegex(smallest["input"], r"^nums=\[-\d\]$")
        self.assertEqual(int(smallest["want"]), -int(smallest["got"]))

    def test_a_fast_that_disagrees_fails_the_case(self):
        r = self.run_it(fast="def solve(nums):\n    return nums[-1]\n")
        self.assertFalse(r["ok"])
        self.assertTrue(any("fast disagrees" in p for p in r["problems"]))

    def test_a_wrong_answer_that_survives_fails_the_case(self):
        r = self.run_it(wrong="def gut(nums):\n    return max(nums)\n\n\ndef planted(nums):\n    return abs(max(nums))\n")
        self.assertFalse(r["ok"])
        self.assertTrue(any("gut survived" in p for p in r["problems"]))

    def test_a_crash_counts_as_a_failure_not_a_stop(self):
        r = self.run_it(wrong="def gut(nums):\n    return nums[99]\n\n\ndef planted(nums):\n    return abs(max(nums))\n")
        self.assertTrue(r["ok"])
        self.assertIn("IndexError", r["subjects"]["gut"]["smallest"]["got"])

    def test_a_broken_slow_machine_fails_the_case(self):
        r = self.run_it(slow="def solve(nums):\n    raise ValueError('no')\n")
        self.assertFalse(r["ok"])
        self.assertIn("slow.py failed", r["problems"][0])

    def test_answers_get_private_copies_of_the_input(self):
        r = self.run_it(fast="def solve(nums):\n    nums.sort()\n    return nums.pop()\n")
        self.assertTrue(r["ok"], r["problems"])

    def test_inputs_are_the_same_for_a_seed_and_differ_between_seeds(self):
        folder = make_case(self.tmp.name)
        one = check.run_case(folder, trials=200, seed=1)["subjects"]["gut"]
        two = check.run_case(folder, trials=200, seed=1)["subjects"]["gut"]
        self.assertEqual(one, two)
        meta = check.load_module(folder / "cases.py", "seed_test_cases")
        self.assertNotEqual(check.generate_inputs(meta, "largest", 50, 1), check.generate_inputs(meta, "largest", 50, 2))

    def test_an_answer_file_replaces_fast_and_skips_the_wrong_answers(self):
        folder = make_case(self.tmp.name)
        good = pathlib.Path(self.tmp.name) / "good.py"
        good.write_text(FAST)
        r = check.run_case(folder, trials=200, answer_path=good)
        self.assertTrue(r["ok"])
        self.assertEqual(list(r["subjects"]), ["answer"])
        bad = pathlib.Path(self.tmp.name) / "bad.py"
        bad.write_text("def solve(nums):\n    return nums[0]\n")
        r = check.run_case(folder, trials=200, answer_path=bad)
        self.assertFalse(r["ok"])
        self.assertGreater(r["subjects"]["answer"]["fails"], 0)

    def test_an_answer_can_be_a_solution_class_with_one_method(self):
        path = pathlib.Path(self.tmp.name) / "cls.py"
        path.write_text("class Solution:\n    def largest(self, nums):\n        return max(nums)\n")
        r = check.run_case(make_case(self.tmp.name), trials=200, answer_path=path)
        self.assertTrue(r["ok"])

    def test_an_answer_with_no_entry_point_is_refused(self):
        path = pathlib.Path(self.tmp.name) / "none.py"
        path.write_text("x = 1\n")
        with self.assertRaises(SystemExit):
            check.load_answer(path)


SIXTEEN_BIT_ANSWER = """
def solve(nums):
    answer = 0
    for bit in range(16):
        if sum((x >> bit) & 1 for x in nums) % 3:
            answer |= 1 << bit
    return answer - (1 << 16) if answer >= 1 << 15 else answer
"""


class LargeInput(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)

    def test_the_16_bit_single_number_answer_is_caught(self):
        path = pathlib.Path(self.tmp.name) / "narrow.py"
        path.write_text(SIXTEEN_BIT_ANSWER)
        r = check.run_case(ROOT / "cases" / "single-number-ii", answer_path=path)
        self.assertFalse(r["ok"])
        self.assertGreater(r["subjects"]["answer"]["fails"], 0)
        problem = [p for p in r["problems"] if "large input" in p]
        self.assertEqual(len(problem), 1, r["problems"])
        self.assertIn("-19979", problem[0])

    def test_the_16_bit_answer_is_also_caught_by_the_large_check_alone(self):
        meta = check.load_module(ROOT / "cases" / "single-number-ii" / "cases.py", "wide_cases")
        path = pathlib.Path(self.tmp.name) / "narrow.py"
        path.write_text(SIXTEEN_BIT_ANSWER)
        args = meta.big(__import__("random").Random(check.DEFAULT_SEED))
        got = check.load_answer(path)(*args)
        self.assertEqual(got, -19979)
        self.assertFalse(meta.big_check(args, got))
        self.assertTrue(meta.big_check(args, -1570393611))

    def test_a_wrong_large_answer_fails_the_case(self):
        cases = CASES_PY + "\n\ndef big_check(args, got):\n    return got == 2\n"
        r = check.run_case(make_case(self.tmp.name, cases=cases), trials=100)
        self.assertFalse(r["ok"])
        self.assertTrue(any("wrong answer" in p for p in r["problems"]))

    def test_a_large_check_that_raises_fails_the_case(self):
        cases = CASES_PY + "\n\ndef big_check(args, got):\n    raise ValueError('no')\n"
        r = check.run_case(make_case(self.tmp.name, cases=cases), trials=100)
        self.assertFalse(r["ok"])

    def test_a_right_large_answer_passes(self):
        cases = CASES_PY + "\n\ndef big_check(args, got):\n    return got == 1\n"
        r = check.run_case(make_case(self.tmp.name, cases=cases), trials=100)
        self.assertTrue(r["ok"], r["problems"])
        self.assertTrue(r["big_checked"])


class Judge(unittest.TestCase):
    def test_a_comparison_that_raises_rejects_the_answer(self):
        def same(args, got, want):
            return sorted(got) == want
        self.assertFalse(check.judge(same, (), 3, [3]))

    def test_a_truthy_comparison_result_is_not_enough(self):
        self.assertFalse(check.judge(lambda a, g, w: "yes", (), 1, 1))

    def test_edges_are_always_tried(self):
        cases = CASES_PY + "\n\ndef edges():\n    return [([-2**31],)]\n"
        with tempfile.TemporaryDirectory() as tmp:
            folder = make_case(tmp, cases=cases, wrong=WRONG)
            meta = check.load_module(folder / "cases.py", "edge_cases")
            inputs = check.generate_inputs(meta, "largest", 5, 1)
            self.assertEqual(inputs[0], ([-2**31],))


class TimedCall(unittest.TestCase):
    @unittest.skipUnless(hasattr(__import__("signal"), "setitimer"), "needs a Unix timer")
    def test_a_hang_is_stopped_and_reported(self):
        def hang():
            while True:
                try:
                    time.sleep(1)
                except Exception:
                    pass
        begun = time.perf_counter()
        ok, detail = check.timed_call(hang, (), 0.1)
        self.assertFalse(ok)
        self.assertIn("no answer within", detail)
        self.assertLess(time.perf_counter() - begun, 1.0)

    def test_a_value_comes_back(self):
        self.assertEqual(check.timed_call(lambda a: a + 1, (1,), 1), (True, 2))


class Table(unittest.TestCase):
    def test_table_is_written_between_the_markers_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            r = check.run_case(make_case(tmp), trials=100)
            page = pathlib.Path(tmp) / "README.md"
            page.write_text(f"before\n{check.TABLE_BEGIN}\nold\n{check.TABLE_END}\nafter\n")
            check.write_table([r], 100, 1, page)
            text = page.read_text()
            self.assertTrue(text.startswith("before\n"))
            self.assertTrue(text.endswith("after\n"))
            self.assertNotIn("old", text)
            self.assertIn("| [largest](largest/) |", text)

    def test_a_pipe_in_an_input_cannot_break_a_row(self):
        self.assertEqual(check.code_cell("a|b"), "`a\\|b`")

    def test_long_inputs_are_cut(self):
        self.assertLessEqual(len(check.code_cell("x" * 500)), 62)


class CommandLine(unittest.TestCase):
    def run_cli(self, *args):
        return subprocess.run([sys.executable, "-B", str(ROOT / "check.py"), *args], capture_output=True, text=True, cwd=ROOT)

    def test_one_case_passes_and_prints_the_smallest_failing_input(self):
        out = self.run_cli("two-sum", "--trials", "500")
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertIn("smallest input:", out.stdout)
        self.assertIn("OK", out.stdout)

    def test_an_unknown_case_is_an_error(self):
        out = self.run_cli("no-such-case")
        self.assertEqual(out.returncode, 2)

    def test_the_list_names_the_cases(self):
        self.assertIn("two-sum", self.run_cli("--list").stdout.split())

    def test_the_bad_example_answer_exits_non_zero(self):
        out = self.run_cli("two-sum", "--answer", "docs/examples/answer_with_a_bug.py", "--trials", "500")
        self.assertEqual(out.returncode, 1)
        self.assertIn("answer", out.stdout)

    def test_the_outside_example_runs(self):
        out = subprocess.run([sys.executable, "-B", str(ROOT / "docs/examples/own_check.py")], capture_output=True, text=True)
        self.assertEqual(out.returncode, 1)
        self.assertRegex(out.stdout, r"smallest failing input: \[-\d\]")


if __name__ == "__main__":
    unittest.main()
