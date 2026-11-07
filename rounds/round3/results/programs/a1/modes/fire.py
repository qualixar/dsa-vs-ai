"""Fire-mode command policy for validated lift positions."""

from typing import Optional


class FireMode:
    """Track normal/fire mode and provide its per-floor command override.

    A new instance starts in normal mode. Only the exact strings ``normal``
    and ``fire`` are accepted; a transition call returns true only when it
    changes the current state.
    """

    def __init__(self):
        self._mode = "normal"

    def set_mode(self, mode: str) -> bool:
        """Set a supported mode, reporting whether state actually changed."""
        if not isinstance(mode, str) or mode not in ("normal", "fire"):
            return False
        if self._mode == mode:
            return False
        self._mode = mode
        return True

    def is_fire(self) -> bool:
        """Return whether fire mode is active."""
        return self._mode == "fire"

    def command(self, floor: int) -> Optional[str]:
        """Return the fire override for a previously validated position."""
        if not self.is_fire():
            return None
        return "open" if floor == 0 else "down"
