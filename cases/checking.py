"""Strict comparisons for the runner and the custom checks in cases.py. A malformed answer must fail, not crash or slip by."""


def is_int(value):
    """True for a real whole number. Python treats True as 1, so a bool does not count."""
    return type(value) is int


def is_ints(value, length=None):
    """A list of whole numbers, of the given length if one is given."""
    return type(value) is list and (length is None or len(value) == length) and all(is_int(x) for x in value)


def is_groups(value, length=None):
    """A list of lists of whole numbers, each of the given length if one is given."""
    return type(value) is list and all(is_ints(group, length) for group in value)


def strict_equal(got, want):
    """Equal, with the same types all the way down, so 1 is not True, 1.0 is not 1 and an object cannot claim equality."""
    if type(got) is not type(want):
        return False
    if type(got) in (list, tuple):
        return len(got) == len(want) and all(strict_equal(a, b) for a, b in zip(got, want))
    return got == want
