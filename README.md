<p align="center">
  <img src="assets/logo.png" alt="Logo" height="96">&nbsp;&nbsp;<img src="assets/banner.svg" alt="DSA vs AI. An answer got cheap. A check didn't." height="96">
</p>

# DSA vs AI

Does a developer still need data structures and algorithms (DSA) when an AI writes the code? This repository holds a three-round test of that question, and a library of 43 classic problems for building the skill the test points at: checking an answer you did not write.

An answer got cheap. A check didn't. Each answer to the newer puzzle in round 1 cost about 3 cents: 50 answers, $1.46 in total ([`rounds/round1/cost.py`](rounds/round1/cost.py)). Knowing whether an answer is right still takes someone who has decided what right means and has built something that can tell.

Film: https://youtu.be/fFENRZjIdto. License: [MIT](LICENSE).

## The result, and its limits

The rule for every round was written before it ran: if the AI can do the job on its own, the round goes to AI.

| Round | Question | Result |
|---|---|---|
| 1. The exam | Can the AI solve two LeetCode Hard problems, 50 times each? | 100 of 100 solutions passed every gate. AI |
| 2. Who checks | Does it catch a one-character bug in code that passes the samples? | 25 of 25 catches, 0 false alarms in 25 clean reads. AI |
| 3. The real job | Can a team of AI agents deliver software whose requirements change four times across five versions, with and without an architect's notes? | On its own: 5 of 5 versions, twice. With notes: 3 of 5, twice. AI |

AI 3, DSA 0, by that rule. That score does not say DSA is dead or that you should skip it. The people who wrote the brief, the limits, the rules and the referee decided what right meant, and those are the parts that stayed with people. The puzzle answers are worth little now. The ability to see a problem's shape and to check a result is what the practice built. Close the notebook of answers, and keep the gym.

**What this does not show.**

- Round 3 is a case study of four runs on one project, a lift controller, which says little about databases or search engines. Those do run on these structures.
- In these four runs the teams that got notes did worse. Four runs cannot say why, and they do not show that the notes caused it.
- Everything here is true of November 2026 models. It is not a benchmark and does not compare models.
- The referee caught 15 of 17 planted bugs that change behaviour. A pass means the 50 days it tried, not every day.

**Earlier runs.** Before this final test, a six-round match ran under other rules: a money cap, a cap on rounds, a hole in the brief and a weaker referee. None of it counts here, and it ended differently, with DSA taking a point when a team stopped on its money cap. Removing those caps helped the AI side. Full account and data: [`rounds/README.md`](rounds/README.md#earlier-runs).

## Try it now

You need Python 3 and nothing else for the library (run on 3.9, 3.13 and 3.15).

```bash
python3 check.py two-sum
```

```
two-sum  [Two Sum]  2977 distinct inputs
  fast     agrees with slow on all 2977
  gut      fails 1253 of 2977
           smallest input: nums=[1, 0, 1], target=1
           got [0, 2], slow says [0, 1]
  planted  fails 132 of 2977
           smallest input: nums=[0, 1], target=0
           got [0, 0], slow says None
  large input: 0.0 s (limit 10 s), answer checked
  OK
```

`slow` is a brute force that is easy to believe. It is the answer key. `fast` is the efficient solution. It must agree with `slow` on every input, and on one large input it must finish in time with an answer that a separate check accepts. `gut` is a tempting wrong idea, and `planted` is the fast solution with one line changed. Both must fail, and the runner prints the smallest input that shows it.

```bash
python3 check.py --all                         # every case, a few seconds on a laptop
python3 check.py two-sum --answer docs/examples/answer_with_a_bug.py   # check any answer file; it runs on your machine, so read it first
python3 -m unittest discover -s tests          # tests for the runner and the library
```

## Start here

**Student.** Pick a case in [`cases/`](cases/README.md), read its README down to the fold and solve it by hand. Run the check, hunt the two bugs, then open the folds. Then give the same problem to any AI and try to break its answer with [`docs/learn.md`](docs/learn.md).

**Working engineer.** Read [`docs/learn.md`](docs/learn.md) and copy [`docs/examples/own_check.py`](docs/examples/own_check.py) for your next piece of AI-written code: a slow machine, a generator, and the smallest failing input, in under 50 lines. The practice of treating an AI's output as untrusted until an independent check passes is one small part of AI Reliability Engineering. For how far checks go on a larger job, read round 3 in [`rounds/README.md`](rounds/README.md).

**Manager.** Read the table and limits above, then ask these three questions of any AI result or any person's. They need no code: How do you know? What would break it? Did someone check it who didn't build it?

## What is in here

| Path | What it is | Type |
|---|---|---|
| [`cases/`](cases/README.md) | 43 problems, each with a slow answer key, a fast solution, and wrong answers shown failing | Practice. No AI was run on it, and it measures none |
| [`check.py`](check.py) | The runner for the library. Standard library only | Tool |
| [`docs/learn.md`](docs/learn.md) | Use this with any AI: check an answer, write a slow machine, plant a bug, say what right means | Guide |
| [`rounds/`](rounds/README.md) | Rounds 1 to 3: tests, the code that was graded, results, and how to rerun them | Evidence |
| [`tests/`](tests/) | Tests for the runner and the library | Tool |

The rounds need more setup than the library: macOS and a virtual environment, as [`rounds/README.md`](rounds/README.md#run-it) explains.
