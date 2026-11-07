# Check an AI's answer yourself

This works with whichever AI you have. You need Python 3 and this repository. Nothing here calls an AI for you, and nothing in the library has been run through one: that step is yours.

## 1. Give the problem to your AI, drop the answer in, run the check

Pick a case and read its README down to the "Hunt the bugs first" heading. Then ask your AI for a Python function named `solve` with the signature that README gives, and save its code to a file. Read the code before you run it, because the next line runs it on your machine.

```bash
python3 check.py two-sum --answer my_answer.py
```

A `Solution` class with one public method also works. The answer must return the type the signature states: `True` does not pass for `1`, and a tuple does not pass for a list. Here is what a failing answer looks like, using the sample in this repository:

```bash
python3 check.py two-sum --answer docs/examples/answer_with_a_bug.py
```

```
two-sum  [Two Sum]  2977 distinct inputs
  answer   fails 541 of 2977
           smallest input: nums=[0, 1], target=0
           got [0, 0], slow says None
  large input: 0.0 s (limit 10 s), answer checked
  PROBLEM: answer disagrees with slow on 541 of 2977 inputs
  FAILED
```

Then read that failing input and work out by hand why the answer is wrong before you ask anyone. A pass means no disagreement on the inputs tried. It does not mean the answer is correct, so also read `cases/<name>/README.md` for what that case's check leaves out.

## 2. Write a slow machine for your own problem

A slow machine is a program so simple that nobody doubts it, which you use as the answer key for anything cleverer.

1. Write down what a right answer is, in one sentence, before writing any code.
2. Write the dumbest program that meets that sentence. Try every order, every pair, every subset. Do not optimise.
3. Check it by hand on three inputs small enough to work out on paper.
4. Generate thousands of small random inputs, including the awkward ones: empty, one item, duplicates, negatives, ties.
5. Compare the code you want to check against the slow machine on all of them, and print the smallest input that disagrees.

`docs/examples/own_check.py` is all of that in one file, for a problem outside the library:

```bash
python3 docs/examples/own_check.py
```

The slow machine has limits. It is still code, so it can be wrong. Keep it short, and use a different method from the fast solution, so that one mistake is less likely to appear in both. And it only works at small sizes: if the fast version is right at size 8 and wrong at size 10,000, you need a separate check at scale, such as the large input in `check.py`, which applies a time limit and tests the answer by another method. A 16-bit mask gets small numbers right and large ones wrong, so try the ends of the range too.

Trying every order stops working very quickly. In round 2 of this repository, it took 4.9 s for 10 requests and 47 s for 11 on the test machine. That is fine, because the slow machine only has to run on small inputs.

## 3. Plant a bug in your own check

A check you have never seen fail tells you little. To test it:

1. Copy a solution you believe is correct.
2. Change one line. Flip a comparison, move a `+ 1`, change a starting value, swap `<` and `<=`.
3. Run the check. It should fail, and it should print a small input you can read.
4. If it passes, either the change does not alter any answer or your check has a hole. Work out which one.

Every case's `wrong.py` has a planted bug, so you can see how each one shows up. Round 2 of this repository did this at a larger scale: of 2,000 single-symbol changes in real solutions, 283 survived every check, some of them because the change did not alter any answer.

## 4. Say what right means before anyone builds

An AI can only be checked against something you wrote down. Before you ask for the code, write:

- **What right means.** Inputs, outputs and the rules that must never break. For a clinic's appointments: no two patients in one slot, no booking outside opening hours, a cancelled slot becomes free again.
- **How you would notice wrong.** A check for each rule that does not depend on the code being checked.
- **When it is done.** Which checks must pass, and on what data. Without this, work can go on after it is already good enough, or stop before it is.

In round 3 of this repository, the people who wrote the brief, the limits and the referee decided what right meant. None of that came from the teams.

## 5. Three questions anyone can ask

You do not have to read code to ask these, of any AI's answer or any person's.

1. How do you know?
2. What would break it?
3. Did someone check it who didn't build it?

## A practice plan

Take one case a day, by hand with no AI, until you can see its shape. Then give the same problem to your AI and try to break its answer with the slow machine. After that, pick something real you understand and build one small thing with AI help, writing down on paper first what right means. In an interview, show the bug your check caught.
