"""Two wrong answers to hunt. Run the check first; README.md explains both behind a fold."""


def gut(intervals):
    """Walk the intervals in the order given, merging each with the one before if they touch."""
    out = []
    for start, end in intervals:
        if out and start <= out[-1][1] and out[-1][0] <= end:
            out[-1] = [min(out[-1][0], start), max(out[-1][1], end)]
        else:
            out.append([start, end])
    return sorted(out)


# A copy of fast.py with exactly one line changed. Find it.
def planted(intervals):
    out = []
    for start, end in sorted(intervals):
        if out and start <= out[-1][1]:
            out[-1][1] = end
        else:
            out.append([start, end])
    return out
