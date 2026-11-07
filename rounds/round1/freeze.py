"""Print one fingerprint (SHA-256) of the grading code and test data.

Run it before generating any solution and show the value on screen; anyone can
rerun it on the published repo and get the same value, which proves the tests
were not changed after the results came in. Candidate solutions and results
are excluded on purpose.
"""
import hashlib
import os

HERE = os.path.dirname(os.path.abspath(__file__))
INCLUDE = ("freeze.py", "grade.py", "runner.py", "report.py", "problems", "tests")


def files():
    for item in INCLUDE:
        path = os.path.join(HERE, item)
        if os.path.isfile(path):
            yield path
        for root, dirs, names in os.walk(path):
            dirs[:] = sorted(d for d in dirs if d != "__pycache__")
            for name in sorted(names):
                if name.endswith((".py", ".md", ".json")):
                    yield os.path.join(root, name)


def fingerprint():
    h = hashlib.sha256()
    for path in files():
        rel = os.path.relpath(path, HERE)
        h.update(rel.encode())
        with open(path, "rb") as f:
            h.update(f.read())
    return h.hexdigest()


def main():
    print(fingerprint())


if __name__ == "__main__":
    main()
