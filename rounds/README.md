# The three rounds: evidence

This folder holds the measured results. The practice library in `cases/` is separate and measures no AI.

Does a developer still need to learn data structures and algorithms (DSA) when an AI writes the code? This repository is a three-round test of that question, with everything needed to rerun it on the next AI that comes out.

The rule for every round was written before it ran: if the AI can do the job on its own, the round goes to AI. DSA takes a round only if the AI could not do it alone and the person who knows DSA made the difference.

| Round | Question | Result |
|---|---|---|
| 1. The exam | Can the AI solve two LeetCode Hard problems, 50 times each? | 100 of 100 solutions passed every gate. AI |
| 2. Who checks | Does it catch a one-character bug in code that passes the samples? | 25 of 25 catches, 0 false alarms in 25 clean reads. AI |
| 3. The real job | Can a team of AI agents deliver software whose requirements change four times across five versions, with and without an architect's notes? | On its own: 5 of 5 versions, twice. With notes: 3 of 5, twice. AI |

Final score: AI 3, DSA 0, by the rule above. Read "What this does not show" before you quote it.

## Run it

You need macOS (the grader uses `sandbox-exec`) and Python 3.10 or newer. Solutions are graded in an environment with the packages in `rounds/round1/requirements.txt`, installed in a virtual environment outside your home folder, because the sandbox blocks reads of the home folder. On macOS, `$TMPDIR` is outside it.

Every block below starts from the root of this repository and ends there, so you can run them in order in one shell.

```bash
python3 -m venv "$TMPDIR/grader-venv"
"$TMPDIR/grader-venv/bin/pip" install -r rounds/round1/requirements.txt
export PY="$TMPDIR/grader-venv/bin/python"
```

```bash
(cd rounds/round1 && $PY -I freeze.py)                              # fingerprint of the grading code and test data
(cd rounds/round1 && $PY -I -m unittest discover -s tests)          # round 1 harness tests itself, several minutes
(cd rounds/round3 && $PY -I -m unittest discover -s tests)          # round 3 referee and scoring tests
```

`freeze.py` prints `a70fee8304f618f752746044dc9da24ac61c1cfaf6280ab24392a6aa3ab786b9`, the same value recorded in every round 1 result file. It covers `grade.py`, `runner.py`, `report.py`, `freeze.py`, `problems/` and `tests/`, all under `rounds/round1/`. Paths are relative to that folder, so moving the folder does not change it.

## Round 1: the exam

Two LeetCode Hard problems, 50 solutions each, from one AI coding agent with no web access, a fresh session per attempt.

| Problem | Why it is here |
|---|---|
| [42. Trapping Rain Water](https://leetcode.com/problems/trapping-rain-water/) | One of the best-known Hard problems; the control |
| [4023. Elevator Requests II](https://leetcode.com/problems/elevator-requests-ii/) | Released 15 Aug 2026 (Biweekly Contest 189), after the stated training cutoff of the model used (June 2026). A cutoff date makes prior exposure unlikely; it cannot prove it |

The prompt was the same for every attempt: "Solve this LeetCode problem in Python 3. Use the given class and method signature. Reply with only the code." followed by the statement verbatim (`rounds/round1/problems/<name>/statement.md`).

Every solution goes through four gates:

| Gate | What it checks |
|---|---|
| 0. Examples | LeetCode's own examples |
| 1. Correctness | Edge cases, 3,000 random small cases against a slow reference that is obviously correct (the elevator reference tries every order), and 600 medium cases against a fast solution that the self-tests check against the reference |
| 2. Scale | The problem's real limits (20,000 bars; 1,500 requests on up to 10^9 floors), 2 seconds per case timed by the grader, 2 GB of memory for the whole process group |
| 3. Sanity | Rules no correct answer can break (water is never negative; the elevator never beats each request's own distance and never loses to a simple sweep) |

**Result:** 50 of 50 survive all four gates on each problem (95% Wilson interval 0.929 to 1.0). Files: `rounds/round1/results/`.

**Cost.** The 50 answers to the elevator problem cost $1.46 in total, an average of 2.9 cents each (median 2.8, range 2.1 to 5.1). The 50 answers to the rain problem averaged 0.5 cents. These are the amounts the agent tool reported for each attempt, in US dollars, at November 2026 prices, so they will not hold for long. Data: `rounds/round1/results/cost_per_answer.csv`.

```bash
python3 rounds/round1/cost.py
```

Rerun on one solution, then summarise it:

```bash
(cd rounds/round1 && $PY -I grade.py elevator candidates/elevator/attempt_01.py --out "$TMPDIR/elevator-one.json")
(cd rounds/round1 && $PY -I report.py "$TMPDIR/elevator-one.json")
```

Rerun a whole problem by pointing `grade.py` at all 50 files (`rounds/round1/candidates/rain/*.py`, `rounds/round1/candidates/elevator/*.py`). To test a new AI, generate your own 50 solutions with the prompt above, put them in a new folder and grade them the same way.

Runtime policy: each batch runs in its own temporary folder inside `sandbox-exec` with no network, no writes outside that folder, and no reads of this repository (so no access to expected answers) or of the home folder. Results return over a private pipe so anything a solution prints cannot corrupt them. A LeetCode-style prelude pre-imports `typing` names and the usual modules. The recursion limit is 10^6 on a 512 MB thread stack. An answer must be a Python `int`. Each solution is also scanned for calls that could interfere with grading (exits, raw writes, clock patching); hits are listed in the results as `flags`. Every result records the solution's SHA-256 and the harness fingerprint.

## Round 2: who checks

Passing the samples proves little. Round 2 asks what does catch a wrong answer, using the 50 real elevator solutions from round 1.

**Wrong strategies.** Four plausible gut answers, checked layer by layer (`rounds/round2/results/wrong_strategies.json`). "Nearest floor first" passes all 3 examples, fails 1 of 7 edge cases, 235 of 3,000 small random cases and 221 of 600 medium ones, and makes passengers wait up to 68.8% longer than the optimum.

**One character.** `rounds/round2/results/planted_one_character.py` is solution 44 with a single comparison changed. It passes the 3 examples and 7 edge cases, then fails 22 cases (8 of the 3,000 small and 14 of the 600 medium):

```bash
(cd rounds/round1 && $PY -I grade.py elevator ../round2/results/planted_one_character.py --out "$TMPDIR/planted.json")
```

**Planted changes.** 2,000 single-symbol changes, 40 in each of the 50 solutions (`rounds/round2/results/planted_changes_summary.json`). 1,499 failed the examples; 182 passed those and failed an edge case; 36 passed those and failed the 3,000 small cases; 283 survived every check, some of them because the change does not alter any answer.

**Brute force does not scale.** Trying every order took 4.9 s for 10 requests and 47 s for 11 on the test machine; 20 requests extrapolate to about 91,000 years, and the real problem has 1,500. The exact method fills a table of about 1.1 million entries in 0.14 s (`rounds/round2/results/brute_force_timing.json`). Timings depend on the machine.

**A fresh reader.** A new AI session with no tools was given the statement and code and asked: "Here is a Python 3 solution to a LeetCode problem. Is this code correct? Reply on the first line with exactly CORRECT or INCORRECT. If it is incorrect, copy the exact line of code that is wrong on the second line, then explain in one sentence." It read the planted-change code 25 times and the correct code 25 times, in shuffled order. It named the wrong line 25 of 25 times and raised 0 false alarms in 25 clean reads, about 10 seconds a read (`rounds/round2/results/fresh_reader.json`). The round's rule: AI takes it with at least 20 catches and at most 5 false alarms. Limit: this tests reading only, not an AI that runs code and writes its own checks.

Rerun the free part (no AI is called; it takes a few minutes):

```bash
$PY -I rounds/round2/checks.py "$TMPDIR/round2"
```

The strategy and planted-change numbers reproduce exactly. The timings change with the machine and its load. To rerun the fresh reader, give your AI the question above with the code from `rounds/round2/results/`, 25 reads of each, in a fresh session without tools.

## Round 3: the real job

**The job.** Software for the lifts of a 30-floor building: one Python class, `Dispatcher`, called with hall calls, button presses inside a lift, a mode change and lift availability; each tick it returns one command per lift (`up`, `down`, `stay`, `open`). A lift carries 10 people. A passenger's time runs from the first call to the tick the doors open at their floor. The exact text is `rounds/round3/brief-v3/BRIEF.md` and the four change requests next to it.

**Five versions, one change at a time.** One lift; three lifts sharing calls; a lift goes out of service and comes back; a fire (every lift must go to floor 0 and open there, none may move up, no doors open on the way); a morning rush of 300 calls in five minutes. A team sees the next change only when its manager signs the last version off.

**The team.** Four agents: a manager (the Lead), two builders (one owns `dispatcher/`, one owns `modes/`) and a reviewer who owns `tests/`. Nobody to ask: where a request is silent the team picks the most consistent reading, writes it down and carries on. The clock is 150 working minutes (time paused on a usage limit does not count). Whatever is in the code when it ends is what ships.

**The referee.** A deterministic simulator the teams never see. It replays scripted days against the team's code in a sandbox and checks four hard rules on every tick (the contract, shaft bounds, the fire rule, no movement while out of service) plus a time limit for every passenger. Each version has 50 days, generated from a stated envelope of traffic (exact call counts, largest crowd, fastest bursts), so no team is held to a day the brief did not allow. A version passes only if all 50 of its days are clean. The limits come from one published procedure (`rounds/round3/calibrate_round3.py`, `rounds/round3/CALIBRATION-ROUND3.json`):

| Version | Everyone arrives within |
|---|---|
| 1 | 270 s |
| 2 | 290 s |
| 3 | 510 s |
| 4 (not counting evacuation) | 590 s |
| 5 | 1850 s, lobby riders' 95th percentile within 1760 s, every rider boarding above the lobby within 190 s |

**How the days were chosen.** The inputs were frozen and hashed, then a random salt was drawn and recorded, then the days were generated from both. `rounds/round3/results/REFEREE-CERTIFICATE.json` lists the hash, the salt, the 50 seeds per version and the SHA-256 of every referee file. The hash also covered the code that drives the agents, which is not published, so it cannot be recomputed here; the certificate and the referee files can be checked (see below).

**Measured before any team ran.** The referee caught all 5 deliberately broken dispatchers. Of 20 bugs planted in a reference solution, 17 changed what the lifts do and the referee caught 15 of those 17. Of 20 bugs planted in an earlier team's code, 9 changed what the lifts do and it caught 6 of those 9. A bug that changes nothing a black-box referee can see cannot be caught by it.

**The two arms.** Same brief, same change requests, same roles, same clock. One arm works on its own (`a1`, `a2`). The other (`b1`, `b2`) also gets one note per version from a senior architect (`rounds/round3/brief-v3/notes/`). The five notes are at most 300 words each. A separate AI session wrote them, working as an architect, with no tools and seeing only the requirements issued so far. No person wrote or edited them. The notes covered how to read each change, the invariants, the cases to test and what "done" means; they did not say when to stop.

**The rule, fixed before any of the four runs.** AI takes the round if the team on its own ships clean (all five versions pass) in both runs. DSA takes it only if the team on its own ships clean fewer than twice, and the team with notes ships clean more often, and passes more versions in total. Otherwise nobody does. Clean counts and version counts are reported whichever way it goes.

### Result

| Run | Arm | Versions passed | How it ended | Working minutes |
|---|---|---|---|---|
| a1 | alone | 5 of 5 | 150-minute deadline reached while its manager had not yet signed version 5; the code passes all five | 151 |
| a2 | alone | 5 of 5 | finished | 80 |
| b1 | notes | 3 of 5 (1, 2, 3) | deadline, still on version 3; version 4 fails because the code has no fire mode, version 5 is clean on 49 of 50 days | 155 |
| b2 | notes | 3 of 5 (1, 2, 5) | deadline, still on version 2; versions 3 and 4 fail because the code lacks the methods they add, 0 of 50 days each | 154 |

The team on its own was clean twice. AI takes the round: AI 3, DSA 0. Data: `rounds/round3/results/RESULT.json`, per run in `rounds/round3/results/teams/<run>/`.

The four shipped programs are in `rounds/round3/results/programs/<run>/` (`dispatcher/`, `modes/` and the team's own `tests/`). Lines of program against lines of tests: a1 259 and 1,339; a2 598 and 774; b1 277 and 1,055; b2 246 and 933.

Unevenness is reported, not corrected: working minutes ran from 80 to 155, and a1, b1 and b2 each had 21 pauses on usage limits against none for a2 (the clock stops during a pause).

**The fire, unscored.** The same day for all four programs: a lift is out from second 414, the alarm sounds at 433 and the lift is back at 443. The two teams on their own had every lift on floor 0 within 20 and 21 seconds with no rule broken. The two teams with notes never reached version 4, so their code had no fire mode; it raised an error at the alarm and the referee logged 50 or more fire-rule violations (the log is capped at 50). Replays, tick by tick: `rounds/round3/results/fire-replay/`.

**A look after the result, unscored.** The referee was also run on each stuck team's code as it stood after its first attempt at the version where it stalled. In four cases that code already passed (b2 version 2 at minute 23, b1 version 3 at 61, a1 version 4 at 34, a1 version 5 at 90) while the manager kept the version open. The teams were never shown referee results. `rounds/round3/results/first_try_passes.json`.

### Rerun round 3

Check that the referee files are the ones the certificate recorded:

```bash
(cd rounds/round3 && $PY -I check_referee.py)
```

It prints the certificate's SHA-256, `ef44851fabd8042d16729dadec34c5b507363c3d7824a41cb78af209b18a8fb5`, `match` for eight referee files and `comment` for two. Three comment lines in those two files changed after certification, to remove private paths; the logic did not change (see the note at the end of this page).

Judge a finished program on the 50 certified days per version. Run on a shipped program:

```bash
(cd rounds/round3 && $PY -I judge_program.py results/programs/a2)
(cd rounds/round3 && $PY -I judge_program.py results/programs/b2)
```

Each takes a few seconds and reproduces the table above, including the first failing day and rule for the versions that fail. Add `--versions v4` to judge one version.

To test a new AI, run your own teams on the brief and change requests in `rounds/round3/brief-v3/` (one file at a time, the next only when the team's manager signs the version off; the notes arm also gets the matching file from `rounds/round3/brief-v3/notes/`), under the same 150 working minutes, then judge each shipped `dispatcher/` and `modes/` with `judge_program.py`. This repository holds the brief, the notes, the referee and the judge; it does not include a driver for any particular agent product. The reference solution and the plain sweep that the limits were calibrated on are `rounds/round3/baselines.py` and `rounds/round3/witness.py`.

## What the numbers mean

Round 1 pass rates are for two problems, one prompt and one agent setup, not a score for AI on Hard problems. Round 2 numbers are counts over 3,000 small and 600 medium generated cases, 2,000 planted changes and 50 reads. Round 3 counts versions that passed a referee on 50 sampled days each. "Clean" means all five versions passed.

## What this does not show

- Four runs. Round 3 is a case study of two runs per arm. Two runs can differ by chance alone, and four cannot tell you why a difference appeared.
- No causal claim about the notes. In these four runs the teams that got notes did worse. That does not show the notes caused it, or that notes of this kind hurt. The notes were written by an AI, were not tested as advice, and never said when to stop.
- One project. A lift controller says little about databases or search engines, which do run on these structures.
- November 2026 models. The same test on the next release can come out differently; that is why it is public.
- A limited referee. It caught 15 of 17 planted bugs that change behaviour, and 6 of 9 in another team's code. A pass means no rule was broken on the 50 days tried, not that no day exists that breaks it.
- Its limits are generous on purpose. The test is about correctness, not speed.
- Round 1 shows the AI solved two stated problems. It does not show the AI could choose what to build or what "right" means. The brief, the limits, the rules and the referee were written by people.
- It is not a benchmark and does not compare models.

## Earlier runs

Before this final test, a six-round match ran under other rules. None of those runs counts here, and they ended differently. The rules then: a money cap, a cap of three rounds per version, a brief with a hole in it (it let every lift be out for any length of time while demanding a time limit), and a referee with three fixed days per version that caught 5 of 20 planted bugs. Two agent setups took part. The first team stopped on its money cap after two versions and the rule gave that round to DSA, so DSA did take a point. A team of the smallest model finished all five versions. Under the second setup the team on its own stopped at version 3 twice (once on the brief's hole, once on a real failure its own tests and the referee had missed), and a supervised team stopped at version 2 because two locked tests were wrong and nobody could edit them. A round of 20 planted bugs went to AI. With the caps removed, a practice team then finished all five versions in about an hour, before the final test was sealed. The final test was rebuilt after that, with 50 generated days per version and the certificate above. Its time limits for versions 1 to 4 and for the rush's lobby riders are looser than the earlier ones, its limit for everyone in the rush is tighter, and the four hard rules are unchanged. Removing the caps helped the AI side. Data: `rounds/earlier-runs/`.

## Layout

- `round1/`: `grade.py`, `runner.py`, `report.py`, `freeze.py` (gates, sandboxed runner, report, fingerprint); `problems/<name>/` with `spec.py` and `statement.md`; `candidates/`, the 100 solutions; `tests/`, self-tests with good and deliberately broken solutions; `results/`
- `round2/`: `checks.py`, the free checks; `results/`
- `round3/`: `brief-v3/` (brief, change requests, notes); `sim.py` and `judge.py` (simulator and sandboxed judge); `scenarios_v3.py` (day generator); `baselines.py` and `witness.py` (known solutions); `calibrate_round3.py`, `referee_certify.py`, `hidden_bugs.py` (bug planting), `judge_program.py`, `check_referee.py`; `tests/`; `results/`, including the shipped programs. `BRIEF.md`, `scenarios.py`, `score.py` and `drift.py` belong to the referee the earlier runs used
- `earlier-runs/`: result data from before the final test

Results files for round 3 and the earlier runs were stripped of tool metadata and run management (cost and usage accounting, identifiers of the tools that ran the agents, local paths, the teams' free-text notes, session counts, rounds per version and setup fingerprints); scored outcomes and working minutes are unchanged. Their hashes therefore no longer match the originals. `teams/<run>/versions.json` now shows only when the manager signed each version off. Without the setup fingerprints, that all four runs shared one setup rests on this statement and can no longer be checked from these files. The certificate, the round 1 files and the fire replays are unmodified. In the shipped programs no code changed; one test method in `rounds/round3/results/programs/b2/tests/test_dispatcher.py` was renamed.

Folders were renamed after the runs (round 3's code was in a folder called `act3`, which is why its temporary folders still use that word). Path lines in `check_referee.py`, `judge_program.py` and `round2/checks.py` changed to match, and `tests/test_round3_brief.py` now reads the note below.

Note on `scenarios_v3.py` and `referee_certify.py`: two comments and one usage line in a docstring changed after certification to remove private paths, and the logic did not change; `round3/results/REFEREE-COMMENT-CHANGE.json` records the old and new hashes, and because the certified originals are not published you can check the new hashes and the unchanged text around those lines, not rehash the originals yourself.
