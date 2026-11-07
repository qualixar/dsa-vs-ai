"""Shared hall-call allocation for multi-lift dispatchers.

The allocator owns no service state: pending calls and car destinations are
snapshots supplied by the dispatcher on each tick.  It remembers only the
previous owner of still-pending floor groups to avoid unnecessary churn.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence


class FirePolicy:
    """Stateless command mapping for an active fire response.

    The dispatcher owns mode and passenger state.  Given its current physical
    floor and availability snapshots, this policy only maps each lift to its
    fire command in stable lift-index order.
    """

    @staticmethod
    def commands(floors_now: Sequence[int], available: Sequence[bool]) -> list[str]:
        """Return one fire command per lift without mutating either snapshot."""
        return [
            "stay" if i >= len(available) or available[i] is not True
            else "open" if floor == 0
            else "down"
            for i, floor in enumerate(floors_now)
        ]


class GroupAllocator:
    """Assign each pending hall floor to one lift using route-aware costs."""

    def __init__(self) -> None:
        self._owners: dict[int, int] = {}

    def reset(self) -> None:
        """Forget owner continuity while leaving all caller-owned work intact."""
        self._owners.clear()

    def assign(
        self,
        t: int,
        floors_now: Sequence[int],
        halls: Mapping[tuple[int, str], int],
        car_targets: Sequence[set[int]],
        directions: Sequence[int],
        can_open: Sequence[bool],
        available: Sequence[bool] | None = None,
    ) -> list[dict[tuple[int, str], int]]:
        """Return per-lift hall snapshots without changing any input.

        Calls at the same floor (including both directions) are indivisible.
        Old calls are allocated first, with travel, current sweep, onboard
        route commitments, and already allocated pickup work reflected in
        each lift's score. A small continuity bonus prevents needless owner
        changes; it never outweighs a materially better or unavailable route.
        """
        count = len(floors_now)
        result: list[dict[tuple[int, str], int]] = [dict() for _ in range(count)]
        if count == 0:
            self._owners.clear()
            return result

        # Availability is a per-index snapshot, not a compacted list. Missing
        # entries are treated as unavailable so malformed snapshots cannot
        # accidentally assign work to an offline lift. The optional argument
        # preserves the historical six-argument API.
        active = ([True] * count if available is None else
                  [i < len(available) and available[i] is True for i in range(count)])
        candidates = [i for i in range(count) if active[i]]

        # Normalize to valid pending floor groups, retaining every input key
        # and its original timestamp. The dispatcher normally validates these.
        groups: dict[int, list[tuple[tuple[int, str], int]]] = {}
        for key, born in halls.items():
            if (isinstance(key, tuple) and len(key) == 2 and
                    type(key[0]) is int and key[0] >= 0 and
                    key[1] in ("up", "down")):
                groups.setdefault(key[0], []).append((key, born))
        self._owners = {floor: owner for floor, owner in self._owners.items()
                        if floor in groups and 0 <= owner < count and active[owner]}

        # No serviceable lift: leave every pending key and timestamp solely in
        # the caller's authoritative snapshot, and remember no stale owners.
        if not candidates:
            return result

        loads = [0] * count
        # Oldest work first reduces starvation; floor is a deterministic tie.
        ordered = sorted(groups, key=lambda floor: (
            min((born for _, born in groups[floor] if type(born) is int), default=t),
            floor,
        ))
        for floor in ordered:
            best = min(candidates, key=lambda lift: self._score(
                lift, floor, floors_now, car_targets, directions, can_open,
                loads, self._owners.get(floor),
            ))
            self._owners[floor] = best
            loads[best] += 1
            for key, born in groups[floor]:
                result[best][key] = born
        return result

    @staticmethod
    def _score(
        lift: int,
        floor: int,
        floors_now: Sequence[int],
        car_targets: Sequence[set[int]],
        directions: Sequence[int],
        can_open: Sequence[bool],
        loads: Sequence[int],
        previous_owner: int | None,
    ) -> tuple[int, int]:
        here = floors_now[lift]
        distance = abs(here - floor)
        sweep = directions[lift] if lift < len(directions) else 0
        targets = car_targets[lift] if lift < len(car_targets) else set()

        # A target in the current sweep is cheap; a target behind the car
        # requires completing the useful forward route before reversing.
        if sweep and (floor - here) * sweep < 0:
            distance += max(2, (max((abs(x - here) for x in targets), default=0) * 2))
        # Existing onboard stops represent committed work and reduce the
        # attractiveness of taking additional hall pickups.
        route_load = len(targets)
        if not sweep and not targets:
            route_load = 0
        score = distance * 4 + route_load * 5 + loads[lift] * 12

        # A lift that just opened here cannot immediately reopen for a capacity
        # recall. Keep the call eligible for another car, or for this car after
        # it has departed, without permanently pinning it elsewhere.
        if lift < len(can_open) and not can_open[lift] and here == floor:
            score += 100
        # Stability is intentionally weak: it breaks near ties but lets a
        # stalled owner lose work to a car that can make useful progress.
        if previous_owner == lift:
            score -= 3
        return score, lift


class RushPolicy:
    """Observable-demand rush advice for normal multi-lift service.

    Detection uses distinct ticks, never event multiplicity. Advice is a
    snapshot: it owns neither halls nor car destinations and returns complete
    hall coverage whenever active.
    """

    ENTRY_WINDOW = 30
    ENTRY_LOBBY_TICKS = 8
    EXIT_QUIET_TICKS = 90

    def __init__(self) -> None:
        self._lobby_ticks: set[int] = set()
        self._other_ticks: set[int] = set()
        self._last_lobby: int | None = None
        self._active = False
        self._allocator = GroupAllocator()

    def reset(self) -> None:
        """Clear detection and continuity state without touching caller work."""
        self._lobby_ticks.clear()
        self._other_ticks.clear()
        self._last_lobby = None
        self._active = False
        self._allocator.reset()

    def observe_call(self, t: int, floor: int, direction: str) -> None:
        """Observe a validated normal hall event; duplicate ticks count once."""
        if type(t) is not int or type(floor) is not int or floor < 0 or direction not in ("up", "down"):
            return
        if floor == 0:
            self._lobby_ticks.add(t)
            self._last_lobby = max(t, self._last_lobby if self._last_lobby is not None else t)
        else:
            self._other_ticks.add(t)
        cutoff = t - self.ENTRY_WINDOW + 1
        self._lobby_ticks = {tick for tick in self._lobby_ticks if cutoff <= tick <= t}
        self._other_ticks = {tick for tick in self._other_ticks if cutoff <= tick <= t}
        if (not self._active and len(self._lobby_ticks) >= self.ENTRY_LOBBY_TICKS and
                len(self._lobby_ticks) >= 2 * len(self._other_ticks)):
            self._active = True

    def plan(self, t, floors_now, halls, car_targets, directions, can_open, available):
        """Return complete per-lift halls and up to two idle lobby stages."""
        if type(t) is not int or not self._active:
            return None
        if (self._last_lobby is None or t - self._last_lobby >= self.EXIT_QUIET_TICKS):
            if not any(type(k) is tuple and len(k) == 2 and k[0] == 0 for k in halls):
                self._active = False
                self._allocator.reset()
                return None
        count = len(floors_now)
        if not count:
            return None
        assignments = self._allocator.assign(
            t, floors_now, halls, car_targets, directions, can_open, available)
        # Stage no more than two genuinely idle cars. One serviceable car is
        # consequently free to answer upstairs demand; target work always wins.
        eligible = [i for i in range(count) if i < len(available) and available[i] is True
                    and i < len(car_targets) and not car_targets[i] and not assignments[i]]
        staging = [None] * count
        stage_count = min(2, max(0, sum(1 for flag in available if flag is True) - 1))
        eligible.sort(key=lambda i: (abs(floors_now[i]), i))
        for i in eligible[:stage_count]:
            staging[i] = 0
        return assignments, staging


__all__ = ["FirePolicy", "GroupAllocator", "RushPolicy"]
