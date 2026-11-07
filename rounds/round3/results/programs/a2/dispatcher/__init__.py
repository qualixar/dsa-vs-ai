"""Small, deterministic collective-control policy for the building lift API."""

from __future__ import annotations

try:
    from modes import GroupAllocator
except ImportError:  # Keep v1 and clean checkouts usable before modes is installed.
    GroupAllocator = None

try:
    from modes import FirePolicy
except ImportError:  # Fire has a local invariant-preserving fallback below.
    FirePolicy = None

try:
    from modes import RushPolicy
except ImportError:  # Rush advice is optional; normal dispatch remains available.
    RushPolicy = None


class Dispatcher:
    """Dispatch lifts using pending car destinations and deduplicated hall calls.

    Hall calls are kept separately by direction so an open can clear both kinds
    while duplicate notifications do not make an old call look new.
    """

    def __init__(self, floors: int, lifts: int):
        # Invalid configuration is reduced to a safe, usable one rather than
        # leaving methods with unusable dimensions.
        self.floors = floors if type(floors) is int and floors > 0 else 1
        self.lifts = lifts if type(lifts) is int and lifts > 0 else 1
        self._hall: dict[tuple[int, str], int] = {}
        self._cars: list[set[int]] = [set() for _ in range(self.lifts)]
        self._available = [True for _ in range(self.lifts)]
        self._direction = [0 for _ in range(self.lifts)]  # -1 down, +1 up
        self._last_floors = [0 for _ in range(self.lifts)]
        # A capacity re-call can arrive while the lift is still stopped at
        # the floor it just opened. Do not trap the lift in repeated opens;
        # that call remains pending for its next visit after it departs.
        self._departed_since_open = [True for _ in range(self.lifts)]
        self._allocator = GroupAllocator() if self.lifts > 1 and GroupAllocator else None
        try:
            self._rush = RushPolicy() if RushPolicy else None
        except Exception:
            self._rush = None
        self._mode = "normal"
        # During fire, late boarding notifications are accepted until this
        # car has been emptied by a fire opening or maintenance transfer.
        self._fire_emptied = [False for _ in range(self.lifts)]

    def set_mode(self, t: int, mode: str) -> None:
        """Change operating mode; repeated or malformed events are harmless."""
        if type(t) is not int or type(mode) is not str or mode not in ("normal", "fire"):
            return
        if mode == self._mode:
            return
        self._mode = mode
        self._reset_allocator()
        self._reset_rush()
        if mode == "fire":
            # Cars already out of service have already been emptied by the
            # building. Active cars remain eligible for delayed car events.
            self._fire_emptied = [not available for available in self._available]
        else:
            self._fire_emptied = [False for _ in range(self.lifts)]
            # A car at ground must be able to board a replayed hall call now.
            self._direction = [0 for _ in range(self.lifts)]
            self._departed_since_open = [True for _ in range(self.lifts)]

    def on_call(self, t: int, floor: int, direction: str) -> None:
        if (type(t) is not int or type(floor) is not int or
                not 0 <= floor < self.floors or type(direction) is not str or
                direction not in ("up", "down")):
            return
        key = (floor, direction)
        if key not in self._hall:
            self._hall[key] = t
        if self._mode == "normal" and self._rush is not None:
            try:
                self._rush.observe_call(t, floor, direction)
            except Exception:
                pass

    def on_car_request(self, t: int, lift: int, floor: int) -> None:
        if (type(t) is not int or type(lift) is not int or
                not 0 <= lift < self.lifts or type(floor) is not int or
                not 0 <= floor < self.floors):
            return
        if (not self._available[lift] or
                (self._mode == "fire" and self._fire_emptied[lift])):
            return
        self._cars[lift].add(floor)

    def set_lift_available(self, t: int, lift: int, available: bool) -> None:
        """Update service state; evacuation itself is performed by the building."""
        if (type(t) is not int or type(lift) is not int or
                not 0 <= lift < self.lifts or type(available) is not bool):
            return
        if self._available[lift] == available:
            return
        self._available[lift] = available
        self._reset_rush()
        if not available:
            # Car requests describe the riders evacuated by the building and
            # cannot be transferred without passenger/direction information.
            self._cars[lift].clear()
            self._direction[lift] = 0
            self._departed_since_open[lift] = True
            if self._mode == "fire":
                self._fire_emptied[lift] = True
        elif self._mode == "fire":
            # Returning cars are empty, and their old route must not reappear.
            self._cars[lift].clear()
            self._direction[lift] = 0
            self._departed_since_open[lift] = True
            self._fire_emptied[lift] = True

    def step(self, t: int, floors_now: list[int]) -> list[str]:
        # A malformed observation has an unambiguous safe fallback.
        if (type(floors_now) is not list or len(floors_now) != self.lifts or
                any(type(f) is not int or not 0 <= f < self.floors for f in floors_now)):
            return ["stay"] * self.lifts

        self._last_floors = list(floors_now)
        if self._mode == "fire":
            commands = self._fire_commands(floors_now)
            for i, command in enumerate(commands):
                if self._available[i] and floors_now[i] == 0 and command == "open":
                    self._cars[i].clear()
                    self._fire_emptied[i] = True
                    self._direction[i] = 0
                    self._departed_since_open[i] = False
            return commands

        rush_plan = self._rush_plan(t, floors_now) if self.lifts > 1 else None
        if rush_plan is not None:
            assigned, staging = rush_plan
        elif self.lifts == 1 and self._available[0]:
            assigned = self._assign_halls(floors_now)
            staging = [None] * self.lifts
        else:
            assigned = self._assign_group_halls(t, floors_now)
            staging = [None] * self.lifts
        # Decide all openings before mutating shared hall state. Required
        # onboard stops always open; each shared pickup floor gets one opener.
        opening = [False] * self.lifts
        for i, here in enumerate(floors_now):
            if not self._available[i]:
                continue
            if self._departed_since_open[i] and here in self._cars[i]:
                opening[i] = True
        pickup_owner: dict[int, int] = {}
        for i, halls in enumerate(assigned):
            if not self._available[i]:
                continue
            if not self._departed_since_open[i]:
                continue
            for floor, _direction in halls:
                pickup_owner.setdefault(floor, i)
        for floor, owner in pickup_owner.items():
            if floors_now[owner] == floor:
                # A drop-off at this floor already serves the hall queue.
                if not any(opening[i] and floors_now[i] == floor for i in range(self.lifts)):
                    opening[owner] = True
        commands: list[str] = []
        for i, here in enumerate(floors_now):
            if not self._available[i]:
                commands.append("stay")
                continue
            halls = assigned[i]
            if opening[i]:
                commands.append("open")
                self._cars[i].discard(here)
                # An opening boards both directions, including a call that
                # might have been assigned to another lift this tick.
                for key in ((here, "up"), (here, "down")):
                    self._hall.pop(key, None)
                # Keep the active sweep through intermediate openings. A
                # capacity re-call can appear behind us after boarding; it
                # must not reverse the car away from destinations already
                # selected by riders aboard. The normal movement logic will
                # choose a new direction once there is no work ahead.
                self._departed_since_open[i] = False
                continue

            targets = set(self._cars[i]) | {f for f, _ in halls}
            # Staging is advisory and only applies to a truly idle car. It
            # never becomes an opening target or displaces passenger work.
            if not targets and staging[i] is not None:
                if here == staging[i]:
                    commands.append("stay")
                    self._direction[i] = 0
                    continue
                targets.add(staging[i])
            if not targets:
                commands.append("stay")
                self._direction[i] = 0
                continue

            direction = self._direction[i]
            ahead = [f for f in targets if (f - here) * direction > 0] if direction else []
            if direction == 0 or not ahead:
                direction = self._choose_direction(i, here, halls)
            # A fresh call can be delivered at the floor we just opened (for
            # example, a capacity re-call on the following tick). It must
            # remain pending while we leave, then be served on our return.
            # Since a same-floor target gives no geometric direction, pick a
            # legal deterministic departure when other work does not already
            # provide one.
            if direction == 0 and any(f == here for f in targets):
                if here < self.floors - 1:
                    direction = 1
                elif here > 0:
                    direction = -1
                elif self.floors == 1:
                    # No departure is possible; service current-floor work.
                    commands.append("open")
                    self._cars[i].discard(here)
                    self._hall.pop((here, "up"), None)
                    self._hall.pop((here, "down"), None)
                    self._departed_since_open[i] = False
                    continue
            if direction == 0:
                commands.append("stay")
            elif direction > 0:
                commands.append("up" if here < self.floors - 1 else "stay")
            else:
                commands.append("down" if here > 0 else "stay")
            if commands[-1] in ("up", "down"):
                self._departed_since_open[i] = True
            self._direction[i] = direction
        return commands

    def _reset_rush(self) -> None:
        if self._rush is not None:
            try:
                reset = getattr(self._rush, "reset", None)
                if callable(reset):
                    reset()
            except Exception:
                pass

    def _rush_plan(self, t: int, floors_now: list[int]):
        """Validate optional policy advice before it can affect dispatch."""
        if self._rush is None or self._mode != "normal":
            return None
        try:
            result = self._rush.plan(
                t, list(floors_now), dict(self._hall),
                [set(x) for x in self._cars], list(self._direction),
                list(self._departed_since_open), list(self._available))
            if result is None or type(result) is not tuple or len(result) != 2:
                return None
            assignments, staging = result
            if (type(assignments) is not list or len(assignments) != self.lifts or
                    any(type(x) is not dict for x in assignments) or
                    type(staging) is not list or len(staging) != self.lifts):
                return None
            expected = set(self._hall)
            seen = set()
            clean = [dict() for _ in range(self.lifts)]
            floor_owner: dict[int, int] = {}
            for i, halls in enumerate(assignments):
                if not self._available[i] and halls:
                    return None
                for key, born in halls.items():
                    if (key not in expected or key in seen or born != self._hall[key]):
                        return None
                    # Both directional queues at a floor are boarded by the
                    # same opening, so advisory policy cannot split ownership.
                    floor = key[0]
                    if floor in floor_owner and floor_owner[floor] != i:
                        return None
                    floor_owner[floor] = i
                    seen.add(key)
                    clean[i][key] = self._hall[key]
            if seen != expected:
                return None
            clean_staging = [None] * self.lifts
            for i, target in enumerate(staging):
                if target is None:
                    continue
                if (not self._available[i] or type(target) is not int or
                        not 0 <= target < self.floors or target != 0 or
                        self._cars[i] or clean[i]):
                    return None
                clean_staging[i] = target
            return clean, clean_staging
        except Exception:
            return None

    def _fire_commands(self, floors_now: list[int]) -> list[str]:
        """Ask the stateless helper, then enforce the required fire mapping."""
        expected = [
            "stay" if not self._available[i] else ("open" if floor == 0 else "down")
            for i, floor in enumerate(floors_now)
        ]
        if FirePolicy is not None:
            try:
                result = FirePolicy().commands(list(floors_now), list(self._available))
                if (type(result) is list and len(result) == self.lifts and
                        result == expected):
                    return result
            except Exception:
                pass
        return expected

    def _reset_allocator(self) -> None:
        if self._allocator is not None:
            try:
                reset = getattr(self._allocator, "reset", None)
                if callable(reset):
                    reset()
            except Exception:
                pass

    def _assign_group_halls(self, t: int, floors_now: list[int]) -> list[dict[tuple[int, str], int]]:
        if self._allocator is not None:
            try:
                result = self._allocator.assign(
                    t, list(floors_now), dict(self._hall),
                    [set(x) for x in self._cars], list(self._direction),
                    list(self._departed_since_open), list(self._available))
                if (type(result) is list and len(result) == self.lifts and
                        all(type(x) is dict for x in result)):
                    # Treat allocator output as advisory. Keep only valid
                    # pending entries assigned to an available car; malformed
                    # output cannot clear authoritative hall state.
                    filtered = [dict() for _ in range(self.lifts)]
                    seen = set()
                    for i, halls in enumerate(result):
                        if not self._available[i]:
                            continue
                        for key, born in halls.items():
                            if key in self._hall and key not in seen:
                                filtered[i][key] = self._hall[key]
                                seen.add(key)
                    if seen == set(self._hall):
                        return filtered
            except Exception:
                pass
        assigned: list[dict[tuple[int, str], int]] = [dict() for _ in range(self.lifts)]
        # Fallback balances pickup floors while accounting for distance and
        # existing onboard route work. Both directions at a floor stay together.
        floors = sorted({floor for floor, _ in self._hall},
                        key=lambda f: (min(self._hall[k] for k in self._hall if k[0] == f), f))
        workload = [0] * self.lifts
        candidates = [i for i, available in enumerate(self._available) if available]
        if not candidates:
            return assigned
        for floor in floors:
            owner = min(candidates, key=lambda i: (
                (self.floors * 4 if floors_now[i] == floor and not self._departed_since_open[i] else 0) +
                abs(floors_now[i] - floor) + sum(abs(x - floors_now[i]) for x in self._cars[i]) // 2
                + workload[i] * max(2, self.floors // 5), i))
            assigned[owner].update({key: born for key, born in self._hall.items() if key[0] == floor})
            workload[owner] += 1
        return assigned

    def _assign_halls(self, floors_now: list[int]) -> list[dict[tuple[int, str], int]]:
        assigned: list[dict[tuple[int, str], int]] = [dict() for _ in range(self.lifts)]
        candidates = [i for i, available in enumerate(self._available) if available]
        if not candidates:
            return assigned
        for key, born in sorted(self._hall.items(), key=lambda item: (item[1], item[0][0], item[0][1])):
            floor, _ = key
            # Deterministic nearest lift assignment, with lift index tie break.
            lift = min(candidates, key=lambda i: (abs(floors_now[i] - floor), i))
            assigned[lift][key] = born
        return assigned

    def _choose_direction(self, lift: int, here: int,
                          halls: dict[tuple[int, str], int]) -> int:
        targets = [(f, -1) for f in self._cars[lift] if f != here]
        targets.extend((f, born) for (f, _), born in halls.items() if f != here)
        if not targets:
            return 0
        # Choose the nearest available stop when beginning or reversing a
        # sweep. Continuing a sweep is handled by step(); favoring age here
        # can send the car across the building past several nearby groups.
        target = min((f for f, _ in targets), key=lambda f: (abs(f - here), f))
        return 1 if target > here else -1
