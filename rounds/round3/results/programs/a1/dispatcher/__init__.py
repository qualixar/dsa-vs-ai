"""Simple, deterministic lift dispatcher.

The building owns physical state; this module owns outstanding button requests.
"""

from __future__ import annotations

from modes.fire import FireMode


class Dispatcher:
    def __init__(self, floors: int, lifts: int):
        self.floors = floors if isinstance(floors, int) and not isinstance(floors, bool) and floors > 0 else 1
        self.lifts = lifts if isinstance(lifts, int) and not isinstance(lifts, bool) and lifts > 0 else 1
        self._hall: dict[tuple[int, str], int] = {}
        self._car: list[dict[int, int]] = [dict() for _ in range(self.lifts)]
        self._direction = [0] * self.lifts
        # Prevent a same-floor crowd re-press from reopening immediately after
        # capacity was reached. The call remains pending for the return sweep.
        self._last_open: list[int | None] = [None] * self.lifts
        self._available = [True] * self.lifts
        self._fire = FireMode()

    def set_mode(self, t: int, mode: str) -> None:
        """Change operating mode; malformed mode values are ignored."""
        if not isinstance(mode, str):
            return
        old_fire = self._fire.is_fire()
        if not self._fire.set_mode(mode):
            return
        if old_fire != self._fire.is_fire():
            # Discard sweep/open guards from the previous operating mode.
            # Pending hall and car obligations remain intact.
            self._direction = [0] * self.lifts
            self._last_open = [None] * self.lifts

    @staticmethod
    def _time(t: int) -> int:
        return t if isinstance(t, int) and not isinstance(t, bool) else 0

    def on_call(self, t: int, floor: int, direction: str) -> None:
        if not isinstance(floor, int) or isinstance(floor, bool) or not 0 <= floor < self.floors:
            return
        if direction not in ("up", "down") or (direction == "up" and floor == self.floors - 1) or (direction == "down" and floor == 0):
            return
        key = (floor, direction)
        self._hall.setdefault(key, self._time(t))

    def on_car_request(self, t: int, lift: int, floor: int) -> None:
        if not isinstance(lift, int) or isinstance(lift, bool) or not 0 <= lift < self.lifts:
            return
        if not self._available[lift]:
            return
        if not isinstance(floor, int) or isinstance(floor, bool) or not 0 <= floor < self.floors:
            return
        self._car[lift].setdefault(floor, self._time(t))

    def set_lift_available(self, t: int, lift: int, available: bool) -> None:
        """Set a lift's service state; withdrawal evacuates its car requests."""
        if not isinstance(lift, int) or isinstance(lift, bool) or not 0 <= lift < self.lifts:
            return
        if not isinstance(available, bool):
            return
        if self._available[lift] == available:
            return
        self._available[lift] = available
        self._direction[lift] = 0
        self._last_open[lift] = None
        if not available:
            self._car[lift].clear()

    def _valid_positions(self, floors_now):
        try:
            if len(floors_now) != self.lifts:
                return None
            positions = list(floors_now)
            if any(not isinstance(p, int) or isinstance(p, bool) or not 0 <= p < self.floors for p in positions):
                return None
            return positions
        except Exception:
            return None

    def step(self, t: int, floors_now: list[int]) -> list[str]:
        positions = self._valid_positions(floors_now)
        if positions is None:
            return ["stay"] * self.lifts
        if self._fire.is_fire():
            commands = []
            for lift, pos in enumerate(positions):
                if not self._available[lift]:
                    commands.append("stay")
                    continue
                command = self._fire.command(pos)
                # command() is defined for validated physical positions.
                commands.append(command)
                if pos == 0:
                    # The opening is issued now and takes effect after step.
                    # Riders leave only on this actual fire-mode opening.
                    self._car[lift].clear()
            return commands
        active = [lift for lift in range(self.lifts) if self._available[lift]]
        # Recompute reservations from this tick's complete snapshot. Pending
        # calls remain in _hall until an opening actually serves their floor.
        reserved: list[set[tuple[int, str]]] = [set() for _ in range(self.lifts)]
        load = [0] * self.lifts
        hall_items = sorted(self._hall.items(), key=lambda item: (item[1], item[0][0], item[0][1]))
        for (floor, way), age in hall_items:
            def cost(lift):
                delta = floor - positions[lift]
                distance = abs(delta)
                direction = self._direction[lift]
                if direction and delta and (1 if delta > 0 else -1) != direction:
                    distance += 2 * (abs(delta) + 1)
                age_credit = min(max(self._time(t) - age, 0), 120) * 0.04
                return (distance + 3 * len(self._car[lift]) + 18 * load[lift] - age_credit, lift)
            if not active:
                break
            owner = min(active, key=cost)
            reserved[owner].add((floor, way))
            load[owner] += 1
        commands = []
        claimed_hall_floors = set()
        for lift, pos in enumerate(positions):
            if not self._available[lift]:
                commands.append("stay")
                continue
            if self._last_open[lift] != pos:
                self._last_open[lift] = None
            car = self._car[lift]
            direction = self._direction[lift]
            blocked_repress = self._last_open[lift] == pos and bool(car) and any(f != pos for f in car)
            hall_here = (not blocked_repress and pos not in claimed_hall_floors
                         and ((pos, "up") in reserved[lift] or (pos, "down") in reserved[lift]))
            if pos in car or hall_here:
                commands.append("open")
                self._last_open[lift] = pos
                car.pop(pos, None)
                self._hall.pop((pos, "up"), None)
                self._hall.pop((pos, "down"), None)
                claimed_hall_floors.add(pos)
                continue

            # Calls served by this sweep: all car stops, plus hall calls in its direction.
            def ahead(d):
                if d > 0:
                    return any(f > pos for f in car) or any(f > pos and way == "up" for f, way in reserved[lift])
                if d < 0:
                    return any(f < pos for f in car) or any(f < pos and way == "down" for f, way in reserved[lift])
                return False

            if direction and not ahead(direction):
                direction = 0
            if direction == 0:
                candidates = []
                candidates.extend((f, age) for f, age in car.items() if f != pos)
                candidates.extend((f, age) for (f, way), age in self._hall.items()
                                  if (f, way) in reserved[lift]
                                  and (f != pos or not blocked_repress))
                if not candidates:
                    self._direction[lift] = 0
                    commands.append("stay")
                    continue
                # Oldest request wins; distance breaks ties deterministically.
                target, _ = min(candidates, key=lambda item: (item[1], abs(item[0] - pos), item[0]))
                direction = 1 if target > pos else -1 if target < pos else 0
                # A target at this floor is necessarily handled above, but tolerate races.
                if direction == 0:
                    commands.append("open")
                    car.pop(pos, None)
                    self._hall.pop((pos, "up"), None)
                    self._hall.pop((pos, "down"), None)
                    continue
            self._direction[lift] = direction
            commands.append("up" if direction > 0 else "down")
        return commands

    def _opened(self, lift: int, floor: int) -> None:
        """Internal hook for integrations that can observe openings."""
        if 0 <= lift < self.lifts and 0 <= floor < self.floors:
            self._car[lift].pop(floor, None)
            self._hall.pop((floor, "up"), None)
            self._hall.pop((floor, "down"), None)
