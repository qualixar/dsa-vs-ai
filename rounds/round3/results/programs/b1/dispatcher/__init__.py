"""Collective lift dispatcher with shared hall calls and car-specific loads."""

from modes import LiftAvailability


class Dispatcher:
    """Dispatch configured lifts using a simple directional sweep."""

    def __init__(self, floors: int, lifts: int):
        self.floors = floors if type(floors) is int and floors > 0 else 1
        self.lifts = lifts if type(lifts) is int and lifts > 0 else 1
        self._hall = set()
        self._owners = {}
        self._car = [dict() for _ in range(self.lifts)]
        self._positions = [0 for _ in range(self.lifts)]
        self._directions = [0 for _ in range(self.lifts)]
        self._availability = LiftAvailability(self.lifts)

    def _valid_floor(self, floor):
        return type(floor) is int and 0 <= floor < self.floors

    def on_call(self, t: int, floor: int, direction: str) -> None:
        if self._valid_floor(floor) and direction in ("up", "down"):
            self._hall.add(floor)

    def on_car_request(self, t: int, lift: int, floor: int) -> None:
        if (type(lift) is int and 0 <= lift < self.lifts
                and self._availability.is_available(lift)
                and self._valid_floor(floor)):
            car = self._car[lift]
            car[floor] = car.get(floor, 0) + 1

    def set_lift_available(self, t: int, lift: int, available: bool) -> None:
        if type(lift) is not int or not 0 <= lift < self.lifts:
            return
        was_available = self._availability.is_available(lift)
        if not self._availability.set_available(lift, available):
            return
        if was_available and not available:
            self._car[lift].clear()
            self._directions[lift] = 0
            self._owners = {floor: owner for floor, owner in self._owners.items()
                            if owner != lift}

    def _eta(self, lift, floor, owned):
        """Approximate ticks to opening, following this car's current sweep."""
        here = self._positions[lift]
        car = self._car[lift]
        direction = self._directions[lift]
        if not car and not owned:
            return abs(floor - here) + 1
        stops = set(car) | set(owned)
        if floor in stops:
            return abs(floor - here) + 1
        ahead = [s for s in stops if direction and (s - here) * direction > 0]
        if not direction or not ahead:
            return abs(floor - here) + 1
        farthest = max(ahead) if direction > 0 else min(ahead)
        distance = abs(farthest - here) + abs(floor - farthest)
        intervening = sum(1 for s in stops if min(here, farthest, floor) <= s <= max(here, farthest, floor))
        return distance + intervening + 1

    def _allocate(self):
        eligible = [i for i, car in enumerate(self._car)
                    if self._availability.is_available(i) and sum(car.values()) < 10]
        owners = {}
        assigned = [set() for _ in range(self.lifts)]
        for floor in sorted(self._hall):
            if not eligible:
                continue
            candidates = [(self._eta(i, floor, assigned[i]), i) for i in eligible]
            best_eta, best = min(candidates)
            old = self._owners.get(floor)
            if old in eligible:
                old_eta = self._eta(old, floor, assigned[old])
                if old_eta - best_eta < 3:
                    best, best_eta = old, old_eta
            owners[floor] = best
            assigned[best].add(floor)
        self._owners = owners
        return assigned

    def step(self, t: int, floors_now: list[int]) -> list[str]:
        if isinstance(floors_now, (list, tuple)):
            for lift in range(min(self.lifts, len(floors_now))):
                if self._valid_floor(floors_now[lift]):
                    self._positions[lift] = floors_now[lift]

        assigned = self._allocate()
        commands = ["stay"] * self.lifts
        opened_halls = set()
        for lift in range(self.lifts):
            if not self._availability.is_available(lift):
                continue
            here = self._positions[lift]
            car = self._car[lift]
            hall = assigned[lift]
            # A hall-only stop is suppressed when full. Own car destinations
            # always remain serviceable, including at a full lift.
            if here in car or (here in hall and sum(car.values()) < 10):
                commands[lift] = "open"
                if here in car:
                    car.pop(here, None)  # unload every rider with this destination
                if here in hall:
                    opened_halls.add(here)
                continue

            targets = (set(car) | hall) - {here}
            if not targets:
                self._directions[lift] = 0
                continue
            direction = self._directions[lift]
            ahead = [f for f in targets if direction and (f - here) * direction > 0]
            if not direction or not ahead or not car:
                target = min(targets, key=lambda f: (abs(f - here), -f))
                direction = 1 if target > here else -1
                self._directions[lift] = direction
            if direction > 0 and here < self.floors - 1:
                commands[lift] = "up"
            elif direction < 0 and here > 0:
                commands[lift] = "down"
            else:
                target = min(targets, key=lambda f: (abs(f - here), -f))
                if target > here:
                    self._directions[lift] = 1
                    commands[lift] = "up"
                elif target < here:
                    self._directions[lift] = -1
                    commands[lift] = "down"

        # The command vector is complete before shared work is consumed. A car
        # opening for its own rider also serves anyone waiting at that floor.
        for lift, command in enumerate(commands):
            if command == "open":
                opened_halls.add(self._positions[lift])
        self._hall.difference_update(opened_halls)
        for floor in opened_halls:
            self._owners.pop(floor, None)
        return commands
