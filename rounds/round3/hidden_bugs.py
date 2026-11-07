"""Single-edit bug planting: list every place one small change can go, and make the change.

Kinds: comparison, arithmetic, and-or, off-by-one, true-false, min-max. `apply_site` edits the syntax tree;
`edit_text` makes the same edit in the original text, so comments and layout survive. The referee certificate
and the round 2 checks both use it, in this order, so a fixed seed picks the same changes everywhere.
"""
import ast
import copy


SWAP_CMP = {ast.Lt: ast.LtE, ast.LtE: ast.Lt, ast.Gt: ast.GtE, ast.GtE: ast.Gt, ast.Eq: ast.NotEq, ast.NotEq: ast.Eq}


SWAP_BIN = {ast.Add: ast.Sub, ast.Sub: ast.Add, ast.Mult: ast.Add}


def sites(tree):
    """Every place one small change can go, as (node index, kind, detail)."""
    out = []
    for i, node in enumerate(ast.walk(tree)):
        if isinstance(node, ast.Compare) and type(node.ops[0]) in SWAP_CMP:
            out.append((i, "comparison", None))
        elif isinstance(node, ast.BinOp) and type(node.op) in SWAP_BIN:
            out.append((i, "arithmetic", None))
        elif isinstance(node, ast.BoolOp):
            out.append((i, "and-or", None))
        elif isinstance(node, ast.Constant) and type(node.value) is int:
            out.append((i, "off-by-one", 1))
            out.append((i, "off-by-one", -1))
        elif isinstance(node, ast.Constant) and type(node.value) is bool:
            out.append((i, "true-false", None))
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in ("min", "max"):
            out.append((i, "min-max", None))
    return out


def apply_site(tree, site):
    tree = copy.deepcopy(tree)
    idx, kind, detail = site
    node = list(ast.walk(tree))[idx]
    if kind == "comparison":
        node.ops[0] = SWAP_CMP[type(node.ops[0])]()
    elif kind == "arithmetic":
        node.op = SWAP_BIN[type(node.op)]()
    elif kind == "and-or":
        node.op = ast.Or() if isinstance(node.op, ast.And) else ast.And()
    elif kind == "off-by-one":
        node.value = node.value + detail
    elif kind == "true-false":
        node.value = not node.value
    elif kind == "min-max":
        node.func.id = "max" if node.func.id == "min" else "min"
    return tree


def _text_between(lines, a, b):
    """Text between two (line, col) points, as utf-8 byte columns the way ast reports them."""
    if a[0] == b[0]:
        return lines[a[0] - 1].encode()[a[1]:b[1]].decode()
    raise ValueError("operator spans lines")


def _replace(lines, line, c0, c1, new):
    raw = lines[line - 1].encode()
    lines[line - 1] = (raw[:c0] + new.encode() + raw[c1:]).decode()


OPS = {ast.Lt: "<", ast.LtE: "<=", ast.Gt: ">", ast.GtE: ">=", ast.Eq: "==", ast.NotEq: "!=", ast.Add: "+", ast.Sub: "-", ast.Mult: "*"}


def edit_text(source, site):
    """One symbol changed in the original text. Proved equal to the tree edit, so comments survive."""
    tree = ast.parse(source)
    idx, kind, detail = site
    node = list(ast.walk(tree))[idx]
    lines = source.split("\n")
    target = None
    if kind in ("off-by-one", "true-false"):
        new = str(node.value + detail) if kind == "off-by-one" else str(not node.value)
        _replace(lines, node.lineno, node.col_offset, node.end_col_offset, new)
        target = node.lineno
    elif kind == "min-max":
        new = "max" if node.func.id == "min" else "min"
        _replace(lines, node.func.lineno, node.func.col_offset, node.func.end_col_offset, new)
        target = node.func.lineno
    else:
        if kind == "comparison":
            left, right, op, to = node.left, node.comparators[0], OPS[type(node.ops[0])], OPS[act3_swap(node.ops[0])]
        elif kind == "arithmetic":
            left, right, op, to = node.left, node.right, OPS[type(node.op)], {ast.Add: "-", ast.Sub: "+", ast.Mult: "+"}[type(node.op)]
        else:  # and-or: every joiner in this one boolean expression
            op = "and" if isinstance(node.op, ast.And) else "or"
            to = "or" if op == "and" else "and"
            for left, right in reversed(list(zip(node.values, node.values[1:]))):
                gap_line = left.end_lineno
                if gap_line != right.lineno:
                    raise ValueError("joiner spans lines")
                gap = _text_between(lines, (gap_line, left.end_col_offset), (right.lineno, right.col_offset))
                _replace(lines, gap_line, left.end_col_offset, right.col_offset, gap.replace(op, to, 1))
                target = gap_line
            return "\n".join(lines), target
        gap = _text_between(lines, (left.end_lineno, left.end_col_offset), (right.lineno, right.col_offset))
        assert op in gap, (op, gap)
        _replace(lines, left.end_lineno, left.end_col_offset, right.col_offset, gap.replace(op, to, 1))
        target = left.end_lineno
    return "\n".join(lines), target


def act3_swap(op):
    return SWAP_CMP[type(op)]
