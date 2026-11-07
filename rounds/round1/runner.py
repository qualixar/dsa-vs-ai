"""Runs one candidate solution on a batch of cases, inside a sandbox, started
by grade.py. Results go to a dedicated pipe (fd given on the command line), so
nothing the candidate prints can corrupt them.

Runtime policy (published in README):
  - LeetCode-style prelude: typing names and common modules are pre-imported,
    so `List[int]` works without an import, as it does on LeetCode.
  - Recursion limit 10**6 on a 512 MB thread stack, so a correct recursive
    solution isn't failed by interpreter settings.
  - Answers must be Python int (not bool). Anything else is recorded by type
    and counted as wrong.
"""
import contextlib
import io
import json
import os
import sys
import threading
import time

PRELUDE = (
    "from typing import *\n"
    "import collections, heapq, bisect, math, itertools, functools, string, re, random\n"
    "from collections import *\nfrom heapq import *\nfrom bisect import *\n"
    "from functools import *\nfrom itertools import *\nfrom math import *\n"
)
MAX_PRINT_CHARS = 100_000


class _Sink(io.TextIOBase):
    """Swallows candidate prints without storing them."""
    def write(self, s):
        return len(s)


def encode(value):
    if type(value) is int:
        return {"value": value, "type": "int"}
    if isinstance(value, int) and not isinstance(value, bool):
        return {"value": int(value), "type": "int"}
    return {"value": None, "type": type(value).__name__, "repr": repr(value)[:120]}


def load_solution(path):
    namespace = {"__name__": "candidate"}
    exec(compile(PRELUDE, "<prelude>", "exec"), namespace)
    source = open(path).read()
    with contextlib.redirect_stdout(_Sink()):
        exec(compile(source, path, "exec"), namespace)
    return namespace["Solution"]


def run_cases(job):
    out = {"results": [], "load_error": None}
    try:
        solution_cls = load_solution(job["candidate"])
    except BaseException as e:  # syntax error, missing class, SystemExit at import
        out["load_error"] = f"{type(e).__name__}: {e}"[:300]
        return out
    for args in job["cases"]:
        t0 = time.perf_counter()
        try:
            with contextlib.redirect_stdout(_Sink()):
                value = getattr(solution_cls(), job["method"])(*args)
            rec = encode(value)
            rec["error"] = None
        except BaseException as e:  # includes SystemExit and RecursionError
            rec = {"value": None, "type": None, "error": f"{type(e).__name__}: {e}"[:300]}
        rec["seconds"] = time.perf_counter() - t0
        out["results"].append(rec)
    return out


def main():
    job = json.load(open(sys.argv[1]))
    proto = os.fdopen(int(sys.argv[2]), "w")
    sys.setrecursionlimit(10**6)
    threading.stack_size(512 * 1024 * 1024)
    box = {}
    t = threading.Thread(target=lambda: box.update(out=run_cases(job)))
    t.start()
    t.join()
    proto.write(json.dumps(box.get("out", {"results": [], "load_error": "runner thread died"})))
    proto.flush()
    os._exit(0)


if __name__ == "__main__":
    main()
