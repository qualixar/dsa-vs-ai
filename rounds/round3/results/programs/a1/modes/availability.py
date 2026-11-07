"""Per-lift availability state for maintenance handling.

The dispatcher owns routing and pending requests. This helper only tracks
whether each lift is currently available for service.
"""


class Availability:
    """Track availability for a fixed set of lifts.

    Lifts start available. ``set_available`` returns ``True`` only when a
    valid lift index receives a real transition and the state is a bool.
    Invalid indexes (including bool indexes) and non-bool states are ignored
    and return ``False``. ``is_available`` returns ``False`` for an invalid
    index. A non-positive or non-integer lift count creates an empty set.
    """

    def __init__(self, lifts: int):
        if isinstance(lifts, int) and not isinstance(lifts, bool) and lifts > 0:
            self._available = [True] * lifts
        else:
            self._available = []

    def set_available(self, lift: int, available: bool) -> bool:
        if not self._valid_lift(lift) or not isinstance(available, bool):
            return False
        if self._available[lift] == available:
            return False
        self._available[lift] = available
        return True

    def is_available(self, lift: int) -> bool:
        return self._valid_lift(lift) and self._available[lift]

    def _valid_lift(self, lift: int) -> bool:
        return (isinstance(lift, int) and not isinstance(lift, bool)
                and 0 <= lift < len(self._available))
