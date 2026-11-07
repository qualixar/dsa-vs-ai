from structures import linked, values_of


def solve(head, k):
    """Copy to a plain list, reverse each full block, rebuild."""
    values = values_of(head)
    out = []
    for i in range(0, len(values), k):
        block = values[i:i + k]
        out += block[::-1] if len(block) == k else block
    return linked(out)
