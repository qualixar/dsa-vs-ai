def solve(s):
    """Keep deleting matched neighbours until nothing changes."""
    while True:
        shorter = s.replace("()", "").replace("[]", "").replace("{}", "")
        if shorter == s:
            return not s
        s = shorter
