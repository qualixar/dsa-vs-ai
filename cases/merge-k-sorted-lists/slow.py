from structures import linked, values_of


def solve(lists):
    """Collect every value, sort, rebuild."""
    values = []
    for head in lists:
        values += values_of(head)
    return linked(sorted(values))
