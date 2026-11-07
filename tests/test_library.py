"""Tests for the case library: every case is complete, and what its README says matches its code."""
import ast
import importlib.util
import pathlib
import random
import re
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
CASES = ROOT / "cases"
sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT))
import check  # noqa: E402

DIRS = check.case_dirs()
TEXT_SUFFIXES = {".py", ".md", ".txt", ".svg", ".json", ".csv"}
SECTIONS = ("**The problem.**", "**Signature here.**", "**The shape to notice.**", "**The idea.**", "**Complexity.**",
            "**How an AI answer to this would be checked.**", "## Hunt the bugs first")


def function_lines(path, name):
    source = path.read_text()
    for node in ast.parse(source).body:
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return source.splitlines()[node.lineno - 1:node.end_lineno]
    raise AssertionError(f"{path} has no function {name}")


def meta_of(folder):
    spec = importlib.util.spec_from_file_location(f"meta_{folder.name.replace('-', '_')}", folder / "cases.py")
    module = importlib.util.module_from_spec(spec)
    if str(CASES) not in sys.path:
        sys.path.insert(0, str(CASES))
    spec.loader.exec_module(module)
    return module


class EveryCase(unittest.TestCase):
    def test_there_are_cases(self):
        self.assertGreaterEqual(len(DIRS), 40)

    def test_every_case_has_its_files(self):
        for folder in DIRS:
            for name in ("README.md", "slow.py", "fast.py", "wrong.py", "cases.py"):
                self.assertTrue((folder / name).is_file(), f"{folder.name}/{name}")

    def test_every_family_is_a_known_family(self):
        for folder in DIRS:
            self.assertIn(meta_of(folder).FAMILY, check.FAMILIES, folder.name)

    def test_every_family_has_a_case(self):
        self.assertEqual({meta_of(f).FAMILY for f in DIRS}, set(check.FAMILIES))

    def test_planted_is_fast_with_exactly_one_line_changed(self):
        for folder in DIRS:
            fast = function_lines(folder / "fast.py", "solve")
            planted = function_lines(folder / "wrong.py", "planted")
            self.assertEqual(len(fast), len(planted), folder.name)
            self.assertEqual(fast[0].replace("def solve(", "def planted("), planted[0], folder.name)
            changed = [(a, b) for a, b in zip(fast[1:], planted[1:]) if a != b]
            self.assertEqual(len(changed), 1, f"{folder.name}: {changed}")

    def test_readme_names_the_exact_planted_line(self):
        for folder in DIRS:
            text = (folder / "README.md").read_text()
            fast = function_lines(folder / "fast.py", "solve")
            planted = function_lines(folder / "wrong.py", "planted")
            old, new = next((a, b) for a, b in zip(fast[1:], planted[1:]) if a != b)
            self.assertIn(f"`{new.strip()}`", text, folder.name)
            self.assertIn(f"`{old.strip()}`", text, folder.name)

    def test_readme_has_every_section_and_hides_the_answers_in_folds(self):
        for folder in DIRS:
            text = (folder / "README.md").read_text()
            for section in SECTIONS:
                self.assertIn(section, text, folder.name)
            self.assertEqual(text.count("<details>"), 2, folder.name)
            self.assertLess(text.index("## Hunt"), text.index("<details>"), folder.name)

    def test_readme_title_and_leetcode_link_match_the_metadata(self):
        for folder in DIRS:
            meta = meta_of(folder)
            text = (folder / "README.md").read_text()
            self.assertTrue(text.startswith(f"# {meta.TITLE}\n"), folder.name)
            number, slug = meta.LEETCODE
            self.assertIn(f"[LeetCode {number}](https://leetcode.com/problems/{slug}/)", text, folder.name)

    def test_nothing_imports_outside_the_standard_library(self):
        if not hasattr(sys, "stdlib_module_names"):
            self.skipTest("this Python cannot list its standard library")
        allowed = set(sys.stdlib_module_names) | {"structures", "checking"}
        for folder in DIRS:
            for path in folder.glob("*.py"):
                for node in ast.walk(ast.parse(path.read_text())):
                    names = []
                    if isinstance(node, ast.Import):
                        names = [a.name for a in node.names]
                    elif isinstance(node, ast.ImportFrom):
                        names = [node.module]
                    for name in names:
                        self.assertIn(name.split(".")[0], allowed, str(path))

    def test_a_case_readme_makes_no_claim_that_an_ai_was_run(self):
        pattern = re.compile(r"\b(the|an|our) AI (wrote|solved|passed|failed|got|answered)\b", re.I)
        for folder in DIRS:
            self.assertIsNone(pattern.search((folder / "README.md").read_text()), folder.name)


class AlwaysEqual:
    """An answer that claims to equal anything."""

    def __eq__(self, other):
        return True

    def __lt__(self, other):
        return False

    def __hash__(self):
        return 0


def first_input(meta, name):
    return check.generate_inputs(meta, name, 200, check.DEFAULT_SEED)


class MalformedAnswers(unittest.TestCase):
    def verdict(self, slug, args, got, want):
        meta = meta_of(CASES / slug)
        return check.judge(getattr(meta, "same", check.equal), args, got, want)

    def test_two_sum_rejects_everything_but_two_valid_indices(self):
        args, want = ([1, 2, 7], 3), [0, 1]
        self.assertTrue(self.verdict("two-sum", args, [0, 1], want))
        self.assertTrue(self.verdict("two-sum", args, [1, 0], want))
        for bad in ([-3, -2], [0.0, 1.0], [0, 1.0], [0], [0, 1, 1], [0, 3], [0, 0], (0, 1), "01", None, [False, True],
                    {0: 1}, AlwaysEqual()):
            self.assertFalse(self.verdict("two-sum", args, bad, want), bad)
        self.assertFalse(self.verdict("two-sum", ([1, 2], 9), [0, 1], None))

    def test_3sum_rejects_malformed_triples(self):
        args, want = ([-1, 0, 1],), [[-1, 0, 1]]
        self.assertTrue(self.verdict("3sum", args, [[1, 0, -1]], want))
        for bad in ([[True, False, -1]], [[-1.0, 0, 1]], [[-1, 0]], [(-1, 0, 1)], [[-1, 0, 1], [-1, 0, 1]], [-1, 0, 1], None, "x"):
            self.assertFalse(self.verdict("3sum", args, bad, want), bad)

    def test_minimum_window_rejects_non_text_and_fake_windows(self):
        args, want = ("abc", "b"), "b"
        self.assertTrue(self.verdict("minimum-window-substring", args, "b", want))
        for bad in (None, 1, ["b"], "a", "z", b"b", AlwaysEqual()):
            self.assertFalse(self.verdict("minimum-window-substring", args, bad, want), bad)

    def test_median_rejects_non_numbers(self):
        args, want = ([1], [2]), 1.5
        self.assertTrue(self.verdict("median-of-two-sorted-arrays", args, 1.5, want))
        self.assertTrue(self.verdict("median-of-two-sorted-arrays", ([1], [3]), 2, 2.0))
        for bad in (None, "1.5", True, [1.5], float("nan"), float("inf"), 1.6):
            self.assertFalse(self.verdict("median-of-two-sorted-arrays", args, bad, want), bad)

    def test_linked_cases_reject_non_lists_and_loops(self):
        from structures import linked
        for slug, args in (("merge-k-sorted-lists", ([linked([1])],)), ("reverse-nodes-in-k-group", (linked([1]), 2))):
            want = linked([1])
            self.assertTrue(self.verdict(slug, args, linked([1]), want))
            for bad in (None, [1], 1, "1", linked([1], 0), linked([1.0]), linked([True]), AlwaysEqual()):
                self.assertFalse(self.verdict(slug, args, bad, want), slug)

    def test_course_schedule_rejects_malformed_orders(self):
        args, want = (2, [[1, 0]]), [0, 1]
        self.assertTrue(self.verdict("course-schedule-ii", args, [0, 1], want))
        for bad in ([1, 0], [False, True], [0.0, 1.0], [0], [0, 1, 1], [0, 5], [-2, -1], (0, 1), None, "01", AlwaysEqual()):
            self.assertFalse(self.verdict("course-schedule-ii", args, bad, want), bad)
        self.assertFalse(self.verdict("course-schedule-ii", (2, [[1, 0], [0, 1]]), [0, 1], []))
        self.assertFalse(self.verdict("course-schedule-ii", (2, [[1, 0], [0, 1]]), None, []))

    def test_combination_sum_rejects_malformed_combinations(self):
        args, want = ([1, 2], 2), [[1, 1], [2]]
        self.assertTrue(self.verdict("combination-sum", args, [[2], [1, 1]], want))
        for bad in ([[True, True], [2]], [[1.0, 1], [2]], [2, [1, 1]], [[1, 1]], [[1, 1], [2], [2]], ((1, 1), (2,)), None, "x"):
            self.assertFalse(self.verdict("combination-sum", args, bad, want), bad)

    def test_every_case_rejects_answers_of_the_wrong_kind(self):
        for folder in DIRS:
            meta = meta_of(folder)
            same = getattr(meta, "same", check.equal)
            slow = check.load_module(folder / "slow.py", f"slow_{folder.name.replace('-', '_')}").solve
            args = first_input(meta, folder.name)[-1]
            want = check.timed_call(slow, args, 10)[1]
            for bad in (AlwaysEqual(), object(), float("nan"), {"a": 1}):
                self.assertFalse(check.judge(same, args, bad, want), folder.name)

    def test_the_default_comparison_is_strict_about_types(self):
        self.assertFalse(check.equal((), True, 1))
        self.assertFalse(check.equal((), 1.0, 1))
        self.assertFalse(check.equal((), [1, 2.0], [1, 2]))
        self.assertFalse(check.equal((), (1, 2), [1, 2]))
        self.assertTrue(check.equal((), [1, [2]], [1, [2]]))


class LargeInputChecks(unittest.TestCase):
    def test_every_case_checks_its_large_answer(self):
        for folder in DIRS:
            self.assertTrue(hasattr(meta_of(folder), "big_check"), folder.name)

    def test_a_large_answer_of_the_wrong_kind_is_rejected(self):
        for folder in DIRS:
            meta = meta_of(folder)
            args = meta.big(random.Random(1))
            for bad in (None, AlwaysEqual(), "nonsense"):
                ok, verdict = check.timed_call(meta.big_check, (args, bad), 60, private_copy=False)
                self.assertFalse(ok and verdict is True, folder.name)

    def test_big_is_the_same_each_time_for_a_seed(self):
        for folder in DIRS:
            meta = meta_of(folder)
            one, two = meta.big(random.Random(1)), meta.big(random.Random(1))
            self.assertEqual(repr(one)[:2000], repr(two)[:2000], folder.name)


class WideIntegers(unittest.TestCase):
    def test_32_bit_ends_are_tried_where_width_or_stand_ins_matter(self):
        for slug in ("single-number-ii", "validate-binary-search-tree", "two-sum", "kth-largest-element-in-an-array",
                     "median-of-two-sorted-arrays", "sliding-window-maximum", "merge-intervals",
                     "binary-tree-maximum-path-sum", "longest-increasing-subsequence", "evaluate-reverse-polish-notation"):
            meta = meta_of(CASES / slug)
            text = repr(meta.edges())
            self.assertTrue("2147483647" in text or "-2147483648" in text, slug)


class ResultsTable(unittest.TestCase):
    def test_the_table_lists_every_case_once(self):
        text = (CASES / "README.md").read_text()
        for folder in DIRS:
            self.assertEqual(text.count(f"| [{folder.name}]({folder.name}/) |"), 1, folder.name)

    def test_a_row_matches_a_fresh_run_on_this_python(self):
        text = (CASES / "README.md").read_text()
        version = ".".join(sys.version.split()[0].split(".")[:2])
        if f"with Python {version}," not in text:
            self.skipTest("the table was written on another Python, where random draws can differ")
        r = check.run_case(CASES / "two-sum")
        rows = check.table_rows([r])
        self.assertIn(rows[-1], text)


class WholeRepo(unittest.TestCase):
    def test_no_text_file_reaches_800_lines_outside_the_evidence(self):
        for path in list(CASES.rglob("*")) + list((ROOT / "docs").rglob("*")) + [ROOT / "check.py", ROOT / "README.md"]:
            if path.is_file() and path.suffix in TEXT_SUFFIXES:
                self.assertLess(len(path.read_text().splitlines()), 800, str(path))

    def test_bytecode_does_not_break_the_text_file_test(self):
        junk = CASES / "two-sum" / "not_text.pyc"
        junk.write_bytes(bytes(range(128, 255)))
        self.addCleanup(junk.unlink)
        self.test_no_text_file_reaches_800_lines_outside_the_evidence()

    def test_readme_commands_name_real_files(self):
        text = (ROOT / "README.md").read_text()
        for link in re.findall(r"\]\(([^)#\s]+)\)", text):
            if not link.startswith("http") and link != "[FILM-URL]":
                self.assertTrue((ROOT / link).exists(), link)


if __name__ == "__main__":
    unittest.main()
