"""Check that the referee files in this folder are the ones the certificate recorded.

  python3 -I check_referee.py

Hashes each file listed under `file_sha256` in results/REFEREE-CERTIFICATE.json and compares. A file may also pass as
`comment  ` when results/REFEREE-COMMENT-CHANGE.json records it: its hash must equal the recorded current hash, and with
the changed text cut out it must equal the recorded hash of the certified file with the same text cut out. Exits 1 on
any other difference. The certificate itself has the SHA-256 printed in rounds/README.md.
"""
import hashlib
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
CERTIFICATE = os.path.join(HERE, "results", "REFEREE-CERTIFICATE.json")
COMMENT_CHANGE = os.path.join(HERE, "results", "REFEREE-COMMENT-CHANGE.json")


def without_changed_text(raw, changed):
    lines = raw.split(b"\n")
    for span in changed:
        lines[span["line"] - 1] = lines[span["line"] - 1][:span["from_column"]]
    return hashlib.sha256(b"\n".join(lines)).hexdigest()


def status(raw, want, change):
    have = hashlib.sha256(raw).hexdigest()
    if have == want:
        return "match   "
    if (change and change["certified_sha256"] == want and change["current_sha256"] == have
            and without_changed_text(raw, change["changed"]) == change["sha256_with_changed_text_removed"]):
        return "comment "
    return "DIFFERS "


def main():
    with open(CERTIFICATE, "rb") as f:
        raw = f.read()
    print(f"certificate sha256 {hashlib.sha256(raw).hexdigest()}")
    recorded = json.loads(raw)["file_sha256"]
    with open(COMMENT_CHANGE) as f:
        record = json.load(f)
    results = []
    for name, want in recorded.items():
        with open(os.path.join(HERE, name), "rb") as f:
            results.append(status(f.read(), want, record["files"].get(name)))
        print(f"  {results[-1]} {name}")
    bad = results.count("DIFFERS ")
    if results.count("comment "):
        print(record["note"])
    print("all referee files check out against the certificate" if not bad else f"{bad} file(s) differ from the certificate")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
