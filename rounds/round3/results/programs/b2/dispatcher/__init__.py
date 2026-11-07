"""Collective-sweep dispatcher with shared hall calls and per-car destinations."""


class Dispatcher:
    """Route a fleet using a sweep per car and one owner per hall floor."""

    # The strict comparison below means this constant of 2 requires a gain
    # of at least 3 whole ticks before an existing owner changes.
    REASSIGN_IMPROVEMENT_TICKS = 2

    def __init__(self, floors: int, lifts: int):
        # The building has floors 0 through 29 even if a caller supplies a
        # larger value. Keep the public constructor tolerant while enforcing
        # the physical top-floor bound in every command path.
        self.floors = min(self._positive_int(floors, 30), 30)
        self.lifts = self._positive_int(lifts, 1)
        self._car_stops = [dict() for _ in range(self.lifts)]
        self._directions = [0 for _ in range(self.lifts)]
        self._opened_here = [None for _ in range(self.lifts)]
        self._car_request_after_open = [False for _ in range(self.lifts)]
        self._hall = set()
        self._owners = {}
        self._positions = [None for _ in range(self.lifts)]

    @staticmethod
    def _positive_int(value, fallback):
        try:
            result = int(value)
        except (TypeError, ValueError, OverflowError):
            return fallback
        return result if result > 0 else fallback

    def _valid_floor(self, floor):
        try:
            converted = int(floor)
            if converted != floor:
                return None
        except (TypeError, ValueError, OverflowError):
            return None
        return converted if 0 <= converted < self.floors else None

    def on_call(self, t: int, floor: int, direction: str) -> None:
        if direction not in ("up", "down"):
            return
        valid = self._valid_floor(floor)
        if valid is not None:
            self._hall.add(valid)

    def on_car_request(self, t: int, lift: int, floor: int) -> None:
        try:
            index = int(lift)
            if index != lift or not 0 <= index < self.lifts:
                return
        except (TypeError, ValueError, OverflowError):
            return
        valid = self._valid_floor(floor)
        if valid is not None:
            stops = self._car_stops[index]
            stops[valid] = stops.get(valid, 0) + 1
            if self._opened_here[index] is not None:
                self._car_request_after_open[index] = True

    def _load(self, lift):
        return sum(self._car_stops[lift].values())

    def _stops(self, lift):
        stops = set(self._car_stops[lift])
        if self._load(lift) < 10:
            stops.update(f for f in self._hall if self._owners.get(f) == lift)
        return stops

    def _eta(self, lift, floor):
        """Ticks until this car opens at floor, following step() tick by tick."""
        current = self._positions[lift]
        if current is None:
            return float("inf")
        direction = self._directions[lift]
        stops = self._stops(lift)
        load = self._load(lift)
        opened_here = self._opened_here[lift]
        request_after_open = self._car_request_after_open[lift]

        # Treat the candidate as a hall stop while projecting, without
        # changing shared state. A new hall call after an open must wait for
        # the post-open departure, just as it does in step().
        if load < 10:
            stops.add(floor)
        for elapsed in range(1, self.floors * 4 + 5):
            own = current in stops
            hall = current == floor and load < 10
            if (own or hall) and (opened_here != current or request_after_open):
                if current == floor:
                    return elapsed
                stops.discard(current)
                opened_here = current
                request_after_open = False
                continue

            if opened_here == current:
                above = any(s > current for s in stops)
                below = any(s < current for s in stops)
                if direction > 0 and above:
                    move = 1
                elif direction < 0 and below:
                    move = -1
                elif above:
                    move = 1
                elif below:
                    move = -1
                elif load >= 10 or current == floor:
                    move = 1 if current < self.floors - 1 else -1
                else:
                    move = 0
                direction = move
                opened_here = None
            else:
                opened_here = None
                above = any(s > current for s in stops)
                below = any(s < current for s in stops)
                if direction > 0 and above:
                    move = 1
                elif direction < 0 and below:
                    move = -1
                elif above:
                    move = 1
                elif below:
                    move = -1
                else:
                    move = 0
                if move:
                    direction = move
            if move and 0 <= current + move < self.floors:
                current += move
        return float("inf")

    def _assign_halls(self):
        # First release ownership that is invalid or no longer capacity eligible.
        for floor, owner in list(self._owners.items()):
            if (floor not in self._hall or owner < 0 or owner >= self.lifts
                    or self._positions[owner] is None or self._load(owner) >= 10):
                self._owners.pop(floor, None)
        for floor in sorted(self._hall):
            if floor in self._owners:
                old = self._owners[floor]
                old_eta = self._eta(old, floor)
                choices = [(self._eta(i, floor), i) for i in range(self.lifts)
                           if self._positions[i] is not None and self._load(i) < 10]
                if choices:
                    new_eta, new = min(choices)
                    if new != old and new_eta + self.REASSIGN_IMPROVEMENT_TICKS < old_eta:
                        self._owners[floor] = new
                continue
            choices = [(self._eta(i, floor), i) for i in range(self.lifts)
                       if self._positions[i] is not None and self._load(i) < 10]
            if choices:
                self._owners[floor] = min(choices)[1]

    def step(self, t: int, floors_now: list[int]) -> list[str]:
        commands = ["stay"] * self.lifts
        if not isinstance(floors_now, (list, tuple)):
            # No position in this tick is authoritative. Invalidate cached
            # positions so hall ownership can be released and reassigned
            # when valid reports resume; keep all demand and car stops.
            self._positions = [None] * self.lifts
            self._assign_halls()
            return commands
        valid_positions = [None] * self.lifts
        try:
            for i in range(min(len(floors_now), self.lifts)):
                valid_positions[i] = self._valid_floor(floors_now[i])
        except (TypeError, ValueError, OverflowError):
            pass
        self._positions = valid_positions
        self._assign_halls()

        # Decide all opens before mutating shared demand. Each car has its own stops.
        opening = [False] * self.lifts
        for i, floor in enumerate(valid_positions):
            if floor is None:
                continue
            own = floor in self._car_stops[i]
            hall = self._owners.get(floor) == i and floor in self._hall and self._load(i) < 10
            if (own or hall) and (self._opened_here[i] != floor or self._car_request_after_open[i]):
                opening[i] = True

        opened_halls = set()
        for i, floor in enumerate(valid_positions):
            if floor is None:
                continue
            if opening[i]:
                commands[i] = "open"
                self._car_stops[i].pop(floor, None)
                self._opened_here[i] = floor
                self._car_request_after_open[i] = False
                # Hall demand belongs to the floor, not its current owner.
                # Any opening there serves the shared queue. This is applied
                # after all opening decisions, before post-step callbacks.
                if floor in self._hall:
                    opened_halls.add(floor)
                continue
            if self._opened_here[i] == floor:
                # Leave after an open so next-tick crowd recalls cannot trap a full car.
                direction = self._directions[i]
                stops = self._stops(i)
                above = any(s > floor for s in stops)
                below = any(s < floor for s in stops)
                if direction > 0 and above:
                    move = 1
                elif direction < 0 and below:
                    move = -1
                elif above:
                    move = 1
                elif below:
                    move = -1
                elif self._load(i) >= 10 or floor in self._hall:
                    move = 1 if floor < self.floors - 1 else -1
                else:
                    move = 0
                self._directions[i] = move
                self._opened_here[i] = None
                if move and 0 <= floor + move < self.floors:
                    commands[i] = "up" if move > 0 else "down"
                continue
            self._opened_here[i] = None
            stops = self._stops(i)
            above = any(s > floor for s in stops)
            below = any(s < floor for s in stops)
            direction = self._directions[i]
            if direction > 0 and above:
                move = 1
            elif direction < 0 and below:
                move = -1
            elif above:
                move = 1
            elif below:
                move = -1
            else:
                move = 0
            if move:
                self._directions[i] = move
                if 0 <= floor + move < self.floors:
                    commands[i] = "up" if move > 0 else "down"
        for floor in opened_halls:
            self._hall.discard(floor)
            self._owners.pop(floor, None)
        return commands
