"""Independent tick simulator and v1 acceptance tests for Dispatcher."""
import random
import unittest

from dispatcher import Dispatcher


FLOORS = 30
CAPACITY = 10
LIMIT = 270
V2_LIMIT = 290


class Passenger:
    def __init__(self, origin, destination, called_at):
        self.origin = origin
        self.destination = destination
        self.called_at = called_at
        self.boarded = False
        self.arrived_at = None
        self.recalled = False


class LiftSimulation:
    """Apply events, ask for commands, then apply movement/opening per brief."""

    def __init__(self, passengers, initially_onboard=()):
        self.dispatcher = Dispatcher(FLOORS, 1)
        self.passengers = list(passengers)
        self.waiting = [[] for _ in range(FLOORS)]
        self.car = []
        self.completed = []
        self.boardings = {}
        self.completions = {}
        self.floor = 0
        self.events = {}
        self.recalls = {}
        for passenger in self.passengers:
            self.events.setdefault(passenger.called_at, []).append(passenger)
        for passenger in initially_onboard:
            passenger.boarded = True
            passenger.called_at = 0
            self.car.append(passenger)
            passenger.board_count = 1
            self.boardings[id(passenger)] = 1
            self.passengers.append(passenger)
            self.dispatcher.on_car_request(0, 0, passenger.destination)
        self.time = 0
        self.next_tick = 0
        self.check_accounting()

    def check_accounting(self):
        locations = [p for q in self.waiting for p in q]
        locations.extend(self.car)
        locations.extend(self.completed)
        scheduled = [p for batch in self.events.values() for p in batch]
        all_locations = locations + scheduled
        assert len(self.car) <= CAPACITY
        assert len({id(p) for p in self.passengers}) == len(self.passengers), "duplicate passenger in master list"
        assert len({id(p) for p in all_locations}) == len(all_locations), "duplicate passenger occupancy"
        assert {id(p) for p in all_locations} == {id(p) for p in self.passengers}, "passenger lost"
        for p in self.passengers:
            ident = id(p)
            assert getattr(p, "board_count", 0) == self.boardings.get(ident, 0)
            assert getattr(p, "completion_count", 0) == self.completions.get(ident, 0)
            assert self.boardings.get(ident, 0) <= 1, "duplicate boarding"
            assert self.completions.get(ident, 0) <= 1, "duplicate completion"
            if p.arrived_at is not None:
                assert self.boardings.get(ident, 0) == self.completions.get(ident, 0) == 1, "completion without exactly one boarding"
                assert p in self.completed and p not in self.car and all(p not in q for q in self.waiting)

    def tick(self, t):
        # External calls are delivered before step. Each passenger presses a
        # hall button; repeated presses at a floor are intentionally preserved.
        for p in self.events.pop(t, ()):
            self.waiting[p.origin].append(p)
            direction = "up" if p.destination > p.origin else "down"
            self.dispatcher.on_call(t, p.origin, direction)
        for floor, direction in self.recalls.pop(t, ()):
            self.dispatcher.on_call(t, floor, direction)

        command = self.dispatcher.step(t, [self.floor])
        assert len(command) == 1
        cmd = command[0]
        assert cmd in {"up", "down", "stay", "open"}
        if cmd == "up":
            assert self.floor < FLOORS - 1
            self.floor += 1
        elif cmd == "down":
            assert self.floor > 0
            self.floor -= 1
        elif cmd == "open":
            # Unload before boarding. The arrival time is this opening tick.
            for p in list(self.car):
                if p.destination == self.floor:
                    self.car.remove(p)
                    p.arrived_at = t
                    p.completion_count = getattr(p, "completion_count", 0) + 1
                    self.completions[id(p)] = self.completions.get(id(p), 0) + 1
                    self.completed.append(p)
            spots = CAPACITY - len(self.car)
            board = self.waiting[self.floor][:spots]
            del self.waiting[self.floor][:len(board)]
            for p in board:
                p.boarded = True
                p.board_count = getattr(p, "board_count", 0) + 1
                self.boardings[id(p)] = self.boardings.get(id(p), 0) + 1
                self.car.append(p)
                self.dispatcher.on_car_request(t, 0, p.destination)
            # People left behind retry their hall button on the next tick.
            if self.waiting[self.floor]:
                direction = "up" if self.waiting[self.floor][0].destination > self.floor else "down"
                # The building issues another hall call whenever people remain
                # after an open. The event is delivered before the next step.
                self.recalls.setdefault(t + 1, []).append((self.floor, direction))
        self.time = t
        self.next_tick = t + 1
        self.check_accounting()

    def run(self, until=3000):
        for t in range(self.next_tick, until + 1):
            self.tick(t)
            if all(p.arrived_at is not None for p in self.passengers):
                return t
        unfinished = [p for p in self.passengers if p.arrived_at is None]
        raise AssertionError(f"unfinished {len(unfinished)} passengers by t={until}")


def make_passengers(specs):
    return [Passenger(o, d, t) for t, o, d in specs]


def validate_envelope(specs):
    if len(specs) != 40:
        raise AssertionError("v1 must contain exactly 40 original arrivals")
    if not all(0 <= t < 600 and 0 <= o < FLOORS and 0 <= d < FLOORS and o != d
               for t, o, d in specs):
        raise AssertionError("invalid v1 arrival")
    if max((sum(1 for x in specs if x[1] == o and x[0] == t)
            for t, o, _ in specs), default=0) > 12:
        raise AssertionError("v1 crowd exceeds 12")
    times = sorted(t for t, _, _ in specs)
    # Half-open rolling windows [start, start+width).
    for width, cap in ((10, 15), (60, 20), (300, 35)):
        left = 0
        for right, t in enumerate(times):
            while times[left] <= t - width:
                left += 1
            if right - left + 1 > cap:
                raise AssertionError((width, right-left+1, t))


def validate_v2_envelope(specs):
    if len(specs) != 120:
        raise AssertionError("v2 must contain exactly 120 original arrivals")
    if not all(0 <= t < 600 and 0 <= o < FLOORS and 0 <= d < FLOORS and o != d
               for t, o, d in specs):
        raise AssertionError("invalid v2 arrival")
    if max((sum(1 for x in specs if x[1] == o and x[0] == t)
            for t, o, _ in specs), default=0) > 15:
        raise AssertionError("v2 crowd exceeds 15")
    times = sorted(t for t, _, _ in specs)
    for width, cap in ((10, 35), (60, 50), (300, 90)):
        left = 0
        for right, t in enumerate(times):
            while times[left] <= t - width:
                left += 1
            assert right - left + 1 <= cap, (width, right-left+1, t)


def designated_burst_day(seed, collide=False):
    """Return a valid day plus stable IDs for its 30 designated burst riders."""
    designated = [(10 + i % 10, i % 3, 20 + i % 3, f"burst-{i}")
                  for i in range(30)]
    # Retry candidate base days when their 300-second concentration cannot
    # accommodate the inserted burst. Keep every attempt reproducible.
    for attempt in range(100):
        specs = random_v2_day(seed + attempt, burst=False)
        incidental_specs = ([row for row in specs if not 10 <= row[0] < 20][:89]
                            if collide else
                            [row for row in specs if not 10 <= row[0] < 20][:90])
        if collide:
            incidental_specs.append((10, 29, 0))
        incidental = [(t, o, d, "aaa-incidental-collision"
                       if collide and i == len(incidental_specs) - 1 else f"incidental-{i}")
                      for i, (t, o, d) in enumerate(incidental_specs)]
        rows = designated + incidental
        rows.sort(key=lambda row: (row[0], row[3]))
        try:
            validate_v2_envelope([row[:3] for row in rows])
        except AssertionError:
            continue
        return rows
    raise AssertionError(f"could not generate valid designated burst day for seed {seed}")


def random_v2_day(seed, crowd=False, burst=False):
    rng = random.Random(seed)
    times = []
    if crowd:
        times.extend([0] * 15)
    if burst:
        # Exactly thirty designated arrivals in a ten-second interval.
        times.extend([10 + (i % 10) for i in range(30)])
    while len(times) < 120:
        t = rng.randrange(600)
        if crowd and t == 0:
            continue
        candidate = times + [t]
        if any(sum(end - width < x <= end for x in candidate) > cap
               for width, cap in ((10, 35), (60, 50), (300, 90))
               for end in candidate):
            continue
        times.append(t)
    specs = []
    for t in sorted(times):
        o = rng.randrange(FLOORS)
        d = rng.randrange(FLOORS - 1)
        if d >= o:
            d += 1
        specs.append((t, o, d))
    if crowd:
        o = rng.randrange(FLOORS)
        d = rng.randrange(FLOORS - 1)
        if d >= o:
            d += 1
        crowd_rows = [(0, o, d)] * 15
        specs = crowd_rows + [row for row in specs if row[0] != 0]
    validate_v2_envelope(specs)
    return specs


class FleetSimulation:
    """Independent multi-car tick model; simultaneous opens share hall demand."""
    def __init__(self, specs, lifts=3, initial_positions=None, initial_riders=None,
                 opening_order="ascending"):
        self.dispatcher = Dispatcher(FLOORS, lifts)
        self.passengers = make_passengers(specs)
        self.waiting = [[] for _ in range(FLOORS)]
        self.cars = [[] for _ in range(lifts)]
        self.completed = []
        self.boardings = {}
        self.completions = {}
        self.floors = list(initial_positions or [0] * lifts)
        if len(self.floors) != lifts:
            raise ValueError("one initial position per lift required")
        self.opening_order = opening_order
        # Preserve only externally generated arrivals as hall events. Initial
        # riders are already aboard and must not be replayed as new calls.
        self.events = {}
        self.recalls = {}
        for p in self.passengers:
            self.events.setdefault(p.called_at, []).append(p)
        for i, riders in enumerate(initial_riders or [[] for _ in range(lifts)]):
            for destination in riders:
                p = Passenger(self.floors[i], destination, 0)
                p.boarded = True
                p.board_count = 1
                self.boardings[id(p)] = 1
                self.cars[i].append(p)
                self.passengers.append(p)
                self.dispatcher.on_car_request(0, i, destination)
        self.next_tick = 0
        self.check_accounting()

    def check_accounting(self):
        locations = [p for queue in self.waiting for p in queue]
        for car in self.cars:
            assert len(car) <= CAPACITY, f"car over capacity: {len(car)}"
            locations.extend(car)
        locations.extend(self.completed)
        assert len({id(p) for p in locations}) == len(locations), (
            "passenger duplicated: " + repr([(p.origin, p.destination, p.called_at,
                                               p.arrived_at, p in self.waiting[p.origin],
                                               any(p in car for car in self.cars))
                                              for p in locations
                                              if sum(q is p for q in locations) > 1][:3]))
        accounted = {id(p) for p in locations}
        master = {id(p) for p in self.passengers}
        assert len(master) == len(self.passengers), "duplicate passenger in master list"
        scheduled = [p for batch in self.events.values() for p in batch]
        assert len({id(p) for p in scheduled}) == len(scheduled), "duplicate future event"
        assert not (accounted & {id(p) for p in scheduled}), "passenger both located and future"
        assert accounted | {id(p) for p in scheduled} == master, "passenger lost"
        for p in self.passengers:
            ident = id(p)
            assert getattr(p, "board_count", 0) == self.boardings.get(ident, 0)
            assert getattr(p, "completion_count", 0) == self.completions.get(ident, 0)
            assert self.boardings.get(ident, 0) <= 1, "duplicate boarding"
            assert self.completions.get(ident, 0) <= 1, "duplicate completion"
            if p.arrived_at is not None:
                assert self.boardings.get(ident, 0) == self.completions.get(ident, 0) == 1, "completion without exactly one boarding"
                assert p in self.completed and all(p not in car for car in self.cars)

    def tick(self, t):
        for p in self.events.pop(t, ()):
            self.waiting[p.origin].append(p)
            self.dispatcher.on_call(t, p.origin, "up" if p.destination > p.origin else "down")
        for floor, direction in self.recalls.pop(t, ()):
            self.dispatcher.on_call(t, floor, direction)
        commands = self.dispatcher.step(t, self.floors[:])
        self.last_commands = commands[:]
        assert len(commands) == len(self.floors)
        assert all(c in {"up", "down", "stay", "open"} for c in commands)
        openings = [i for i, c in enumerate(commands) if c == "open"]
        if self.opening_order == "reverse":
            openings.reverse()
        for i, cmd in enumerate(commands):
            f = self.floors[i]
            assert not (cmd == "up" and f == FLOORS - 1)
            assert not (cmd == "down" and f == 0)
            if cmd == "up": self.floors[i] += 1
            elif cmd == "down": self.floors[i] -= 1
        # Unload the complete batch first. Boarding order is selectable for
        # deterministic simulator coverage; ascending is the default convention.
        for i in openings:
            f = self.floors[i]
            for p in list(self.cars[i]):
                if p.destination == f:
                    self.cars[i].remove(p)
                    p.arrived_at = t
                    p.completion_count = getattr(p, "completion_count", 0) + 1
                    self.completions[id(p)] = self.completions.get(id(p), 0) + 1
                    self.completed.append(p)
        for i in openings:
            f = self.floors[i]
            free = CAPACITY - len(self.cars[i])
            board = self.waiting[f][:free]
            del self.waiting[f][:len(board)]
            for p in board:
                p.boarded = True
                p.board_count = getattr(p, "board_count", 0) + 1
                self.boardings[id(p)] = self.boardings.get(id(p), 0) + 1
                self.cars[i].append(p)
                self.dispatcher.on_car_request(t, i, p.destination)
            if self.waiting[f]:
                p = self.waiting[f][0]
                self.recalls.setdefault(t + 1, []).append(
                    (f, "up" if p.destination > f else "down"))
        self.check_accounting()
        self.next_tick = t + 1

    def run(self, until=3000):
        for t in range(self.next_tick, until + 1):
            self.tick(t)
            if all(p.arrived_at is not None for p in self.passengers):
                return t
        raise AssertionError(f"unfinished passengers by t={until}")


def random_day(seed, crowd=False):
    rng = random.Random(seed)
    times = [0] * 12 if crowd else []
    # Rejection sampling against the actual half-open rolling windows keeps
    # the schedule admissible while spreading the 40 calls over ten minutes.
    target = 40 if not crowd else 40
    while len(times) < target:
        t = rng.randrange(600)
        candidate = times + [t]
        if any(sum(end - width < x <= end for x in candidate) > cap
               for width, cap in ((10, 15), (60, 20), (300, 35))
               for end in candidate):
            continue
        times.append(t)
    specs = []
    for t in sorted(times):
        o = rng.randrange(FLOORS)
        d = rng.randrange(FLOORS - 1)
        if d >= o:
            d += 1
        specs.append((t, o, d))
    if crowd:
        # Use one same-origin, same-destination 12-person batch at t=0.
        o = rng.randrange(FLOORS)
        d = rng.randrange(FLOORS - 1)
        if d >= o:
            d += 1
        specs[:12] = [(0, o, d)] * 12
    validate_envelope(specs)
    return specs


class DispatcherTests(unittest.TestCase):
    def test_safety_and_bad_inputs_never_raise(self):
        d = Dispatcher(30, 1)
        for _ in range(3):
            self.assertEqual(d.step(0, [0]), ["stay"])
        d.on_call(0, -1, "up")
        d.on_call(0, 30, "down")
        d.on_call(0, 4, "sideways")
        d.on_car_request(0, 0, 30)
        self.assertEqual(d.step(0, []), ["stay"])
        self.assertEqual(d.step(0, [999]), ["stay"])
        self.assertEqual(Dispatcher(30, 2).step(0, [0, 0]), ["stay", "stay"])

    def test_idle_floor_zero_call_at_top_floor(self):
        d = Dispatcher(30, 1)
        d.on_call(0, 29, "down")
        self.assertEqual(d.step(0, [0]), ["up"])
        for floor in range(1, 29):
            self.assertEqual(d.step(floor, [floor]), ["up"])
        self.assertEqual(d.step(29, [29]), ["open"])

    def test_current_floor_both_directions_and_duplicate_calls(self):
        d = Dispatcher(30, 1)
        d.on_call(0, 0, "up")
        d.on_call(0, 0, "down")
        d.on_call(0, 0, "up")
        self.assertEqual(d.step(0, [0]), ["open"])
        self.assertEqual(d.step(1, [0]), ["stay"])

    def test_arrival_during_open_tick_survives_and_car_request_is_served(self):
        d = Dispatcher(30, 1)
        d.on_call(0, 0, "up")
        self.assertEqual(d.step(0, [0]), ["open"])
        # Events generated by applying open are delivered after that step.
        d.on_call(0, 0, "up")
        d.on_car_request(0, 0, 3)
        self.assertEqual(d.step(1, [0]), ["open"])
        self.assertEqual(d.step(2, [0]), ["up"])
        self.assertEqual(d.step(3, [1]), ["up"])
        self.assertEqual(d.step(4, [2]), ["up"])
        self.assertEqual(d.step(5, [3]), ["open"])

    def test_12_person_crowd_requires_recall_and_all_arrive(self):
        passengers = make_passengers([(0, 0, 8)] * 12)
        sim = LiftSimulation(passengers)
        sim.run(100)
        self.assertTrue(all(p.arrived_at is not None for p in passengers))

    def test_initially_onboard_t0_rider(self):
        rider = Passenger(0, 4, 0)
        sim = LiftSimulation([], initially_onboard=[rider])
        sim.run(30)
        self.assertEqual(rider.arrived_at, 4)  # 4 moves, then opens.

    def test_v1_tick_then_run_delivers_t0_and_later_arrivals_once(self):
        passengers = make_passengers([(0, 0, 2), (3, 8, 9)])
        sim = LiftSimulation(passengers)
        sim.tick(0)
        self.assertEqual(sim.next_tick, 1)
        sim.run(100)
        self.assertEqual([p.arrived_at is not None for p in passengers], [True, True])
        self.assertEqual(len(sim.events), 0)
        self.assertEqual(len(sim.passengers), 2)

    def test_seeded_envelope_days_all_individual_times_within_limit(self):
        seeds = list(range(50)) + [1001, 2026, 8675309]
        worst = (0, None, None, None)
        failures = []
        for seed in seeds:
            specs = random_day(seed, crowd=(seed % 5 == 0))
            sim = LiftSimulation(make_passengers(specs))
            try:
                sim.run()
            except AssertionError as exc:
                failures.append((seed, "unfinished", str(exc)))
                continue
            max_time = max(p.arrived_at - p.called_at for p in sim.passengers)
            slowest = max(sim.passengers,
                          key=lambda p: p.arrived_at - p.called_at)
            if max_time > worst[0]:
                worst = (max_time, seed, specs, slowest)
            if max_time > LIMIT:
                failures.append((seed, max_time, "over 270 seconds"))
        self.assertFalse(failures,
                         f"{len(seeds)} days; worst={worst[0]}s seed={worst[1]}; "
                         f"margin={LIMIT-worst[0]}s; failures={failures}")
        print(f"v1 sample: {len(seeds)} days; worst={worst[0]}s seed={worst[1]}; "
              f"passenger=({worst[3].origin}->{worst[3].destination}, "
              f"call={worst[3].called_at}, arrival={worst[3].arrived_at}); "
              f"margin={LIMIT-worst[0]}s")

    def test_v2_fixed_shared_hall_cases(self):
        # Equidistant calls resolve deterministically and only one lift is sent.
        d = Dispatcher(30, 3)
        d.on_call(0, 10, "up")
        commands = d.step(0, [8, 12, 20])
        self.assertEqual(commands.count("up") + commands.count("down"), 1)
        # Cars can open together for separate hall floors.
        d = Dispatcher(30, 3)
        d.on_call(0, 5, "up")
        d.on_call(0, 8, "up")
        self.assertEqual(d.step(0, [5, 8, 20]), ["open", "open", "stay"])
        # A full lift cannot consume a hall floor; another car can own it.
        d = Dispatcher(30, 2)
        d.on_call(0, 10, "up")
        for floor in range(20, 30):
            d.on_car_request(0, 0, floor)
        commands = d.step(0, [9, 0])
        self.assertEqual(commands[0], "up")
        self.assertEqual(commands[1], "up")
        # Trace through the waiting floor: the full car passes without opening,
        # while the eligible car serves the shared hall call.
        for t, floors in enumerate(([10, 1], [11, 2], [12, 3], [13, 4],
                                    [14, 5], [15, 6], [16, 7], [17, 8],
                                    [18, 9], [19, 10]), 1):
            commands = d.step(t, list(floors))
            self.assertNotEqual(commands[0], "open")
            if floors[0] == 10:
                self.assertIn(10, d._hall)
        self.assertNotIn(10, d._hall)

    def test_v2_owner_tie_keeps_owner_and_clear_gain(self):
        d = Dispatcher(30, 3)
        d.on_call(0, 10, "up")
        d.step(0, [8, 12, 20])
        self.assertEqual(d._owners[10], 0)  # deterministic lower-index tie
        # One-step advantage is below the documented reassignment threshold.
        d.step(1, [8, 11, 20])
        self.assertEqual(d._owners[10], 0)
        # A clear improvement transfers ownership.
        d.step(2, [0, 9, 20])
        self.assertEqual(d._owners[10], 1)

    def test_v2_car_work_survives_invalid_position_reports(self):
        d = Dispatcher(30, 2)
        d.on_car_request(0, 0, 6)
        d.on_call(0, 20, "up")
        self.assertEqual(d.step(0, [0, 29]), ["up", "down"])
        self.assertEqual(d.step(1, [None, 28]), ["stay", "down"])
        self.assertEqual(d.step(2, "missing"), ["stay", "stay"])
        self.assertEqual(d.step(3, [1, 27]), ["up", "down"])

    def test_v2_all_full_cars_keep_repeated_destination_requests(self):
        d = Dispatcher(30, 3)
        for car in range(3):
            for _ in range(10):
                d.on_car_request(0, car, 5)
        d.on_call(0, 5, "up")
        self.assertEqual(d.step(0, [0, 10, 20]), ["up", "down", "down"])
        # Each count is retained after other cars reach/open at the same floor.
        self.assertEqual(d.step(1, [1, 9, 19]), ["up", "down", "down"])

    def test_simulator_accounting_detects_corruption(self):
        factories = [lambda: LiftSimulation(make_passengers([(2, 0, 1)])),
                     lambda: FleetSimulation([(2, 0, 1)], 2)]
        for factory in factories:
            sim = factory()
            p = sim.passengers[0]
            sim.passengers.append(p)
            with self.assertRaisesRegex(AssertionError, "duplicate passenger"):
                sim.check_accounting()
            sim.passengers.pop()
            sim.events[99] = [p, p]
            with self.assertRaises(AssertionError):
                sim.check_accounting()
            sim.events.pop(99)
            original = sim.events.pop(2)
            with self.assertRaisesRegex(AssertionError, "passenger lost"):
                sim.check_accounting()
            sim.events[2] = original
            if isinstance(sim, LiftSimulation):
                sim.waiting[0].append(p)
                with self.assertRaises(AssertionError):
                    sim.check_accounting()
                sim.waiting[0].pop()
            else:
                sim.waiting[0].append(p)
                with self.assertRaises(AssertionError):
                    sim.check_accounting()
                sim.waiting[0].pop()
            if isinstance(sim, LiftSimulation):
                sim.car.extend([p] * (CAPACITY + 1))
                with self.assertRaises(AssertionError): sim.check_accounting()
            else:
                sim.cars[0].extend([p] * (CAPACITY + 1))
                with self.assertRaises(AssertionError): sim.check_accounting()

    def test_simultaneous_open_queue_has_exactly_once_service_both_orders(self):
        for order in ("ascending", "reverse"):
            sim = FleetSimulation([(0, 10, 2)] * 15, 3, [10, 10, 29],
                                  [[10], [10], []], opening_order=order)
            sim.tick(0)
            self.assertEqual(sim.last_commands[:2], ["open", "open"])
            sim.run(100)
            self.assertTrue(all(p.board_count == p.completion_count == 1
                                for p in sim.passengers))
            self.assertFalse(sim.waiting[10])

    def test_v2_seeded_days_and_v1_single_lift_regression(self):
        seeds = list(range(30)) + [1001, 2026, 8675309]
        worst = (0, None, None)
        failures = []
        for seed in seeds:
            specs = random_v2_day(seed, crowd=(seed % 4 == 0), burst=(seed % 5 == 0))
            sim = FleetSimulation(specs, 3)
            try:
                sim.run()
            except AssertionError as exc:
                failures.append((seed, str(exc)))
                continue
            elapsed = max(p.arrived_at - p.called_at for p in sim.passengers)
            slowest = max(sim.passengers,
                          key=lambda p: p.arrived_at - p.called_at)
            if elapsed > worst[0]:
                worst = (elapsed, seed, slowest)
            if elapsed > V2_LIMIT:
                failures.append((seed, elapsed))
        self.assertFalse(failures,
                         f"v2 {len(seeds)} days; worst={worst[0]}s seed={worst[1]}; "
                         f"margin={V2_LIMIT-worst[0]}s; failures={failures}")
        print(f"v2 initial sample: {len(seeds)} days; worst={worst[0]}s seed={worst[1]}; "
              f"passenger=({worst[2].origin}->{worst[2].destination}, "
              f"call={worst[2].called_at}, arrival={worst[2].arrived_at}); "
              f"margin={V2_LIMIT-worst[0]}s")
        # Keep the one-car v1 contract under its original traffic envelope.
        worst_v1 = (0, None, None)
        for seed in range(12):
            sim = LiftSimulation(make_passengers(random_day(2000 + seed)))
            sim.run()
            slowest = max(sim.passengers,
                          key=lambda p: p.arrived_at - p.called_at)
            elapsed = slowest.arrived_at - slowest.called_at
            if elapsed > worst_v1[0]:
                worst_v1 = (elapsed, 2000 + seed, slowest)
        self.assertLessEqual(worst_v1[0], LIMIT, f"v1 regression worst={worst_v1[0]}s")
        print(f"v1 regression sample: 12 days; worst={worst_v1[0]}s seed={worst_v1[1]}; "
              f"passenger=({worst_v1[2].origin}->{worst_v1[2].destination}, "
              f"call={worst_v1[2].called_at}, arrival={worst_v1[2].arrived_at}); "
              f"margin={LIMIT-worst_v1[0]}s")

    def test_envelope_validators_reject_invalid_days(self):
        with self.assertRaises(AssertionError): validate_envelope([(0, 0, 1)] * 39)
        with self.assertRaises(AssertionError): validate_envelope([(0, 0, 0)] * 40)
        with self.assertRaises(AssertionError): validate_v2_envelope([(600, 0, 1)] * 120)
        with self.assertRaises(AssertionError): validate_v2_envelope([(0, 0, 1)] * 16 + [(100, 1, 2)] * 104)

    def test_envelope_validator_count_tick_endpoints_and_half_open_windows(self):
        # Independently valid days put arrivals exactly one window-width apart;
        # half-open windows must not count both endpoints together.
        v1 = [(i * 15, i % 29, i % 29 + 1) for i in range(40)]
        v2 = [(i * 5, i % 29, i % 29 + 1) for i in range(120)]
        validate_envelope(v1)
        validate_v2_envelope(v2)

        for validator, rows, expected in (
                (validate_envelope, v1, 40), (validate_v2_envelope, v2, 120)):
            with self.assertRaises(AssertionError): validator(rows[:-1])
            for bad in ((-1, 0, 1), (600, 0, 1), (0, -1, 1), (0, 0, 30),
                        (0, 2, 2)):
                broken = list(rows)
                broken[0] = bad
                with self.assertRaises(AssertionError, msg=f"validator accepted {bad}"):
                    validator(broken)

    def test_envelope_validator_exact_rate_caps_and_reason_specific_excess(self):
        # Keep every other rolling cap below its limit; these fixtures are
        # deliberately constructed rather than drawn by the rejection sampler.
        for validator, count, caps in ((validate_envelope, 40, ((10, 15), (60, 20), (300, 35))),
                                       (validate_v2_envelope, 120, ((10, 35), (60, 50), (300, 90)))):
            for width, cap in caps:
                remaining = count - cap
                if width == 10:
                    # One arrival per tick in the target half-open window.
                    times = [i % 10 for i in range(cap)] + [300 + (299 * i) // remaining
                                                for i in range(remaining)]
                elif width == 60:
                    times = [(60 * i) // cap for i in range(cap)] + [100 + (499 * i) // remaining
                                                           for i in range(remaining)]
                else:
                    times = [(299 * i) // cap for i in range(cap)] + [300 + (299 * i) // remaining
                                                                      for i in range(remaining)]
                rows = [(t, i % 29, i % 29 + 1) for i, t in enumerate(sorted(times))]
                # For exact 10/60/300 caps, selected first cap points attain it.
                validator(rows)
                self.assertEqual(len(rows), count)
                bad_times = list(times)
                bad_times[cap] = bad_times[0]
                bad = [(t, i % 29, i % 29 + 1) for i, t in enumerate(sorted(bad_times))]
                with self.assertRaises(AssertionError, msg=f"missed cap+1 width={width} cap={cap} count={count}") as caught:
                    validator(bad,)
                self.assertEqual(caught.exception.args[0][0], width)
                self.assertEqual(caught.exception.args[0][1], cap + 1)

    def test_envelope_validator_exact_and_excess_crowd_boundaries(self):
        for validator, count, limit, reason in (
                (validate_envelope, 40, 12, "v1 crowd exceeds 12"),
                (validate_v2_envelope, 120, 15, "v2 crowd exceeds 15")):
            remainder = count - limit
            times = [0] * limit + [100 + (499 * i) // remainder
                                    for i in range(remainder)]
            exact = [(t, 0 if i < limit else i % 29,
                      1 if i < limit else i % 29 + 1)
                     for i, t in enumerate(times)]
            validator(exact)
            self.assertEqual(sum(t == 0 and o == 0 for t, o, _ in exact), limit)
            excessive = list(exact)
            excessive[limit] = (0, 0, 1)
            with self.assertRaisesRegex(AssertionError, reason):
                validator(excessive)

    def test_v2_former_hall_pursuer_stops_after_cross_owner_clear(self):
        d = Dispatcher(30, 2)
        d.on_call(0, 5, "up")
        d._owners[5] = 0
        d.on_car_request(0, 1, 5)
        self.assertEqual(d.step(0, [3, 5]), ["up", "open"])
        self.assertNotIn(5, d._hall)
        self.assertEqual(d.step(1, [4, 5]), ["stay", "stay"])

    def test_v2_full_car_passenger_boards_and_completes(self):
        sim = FleetSimulation([(0, 10, 15)], 2, [9, 0],
                              [[20, 21, 22, 23, 24, 25, 26, 27, 28, 29], []])
        sim.tick(0)
        self.assertEqual(sim.last_commands, ["up", "up"])
        self.assertEqual(sim.floors, [10, 1])
        sim.tick(1)
        self.assertEqual(sim.floors, [11, 2])
        self.assertEqual(len(sim.cars[0]), CAPACITY)
        self.assertNotEqual(sim.last_commands[0], "open")
        self.assertTrue(sim.waiting[10])
        self.assertIn(10, sim.dispatcher._hall)
        self.assertEqual(len(sim.cars[0]), 10)
        eligible_open_seen = False
        for t in range(2, 20):
            sim.tick(t)
            if sim.last_commands[1] == "open" and sim.floors[1] == 10:
                eligible_open_seen = True
                self.assertIn(sim.passengers[0], sim.cars[1])
                break
        self.assertTrue(eligible_open_seen, "eligible car never opened at floor 10")
        passenger = sim.passengers[0]
        self.assertEqual(passenger.board_count, 1)
        sim.run(100)
        self.assertEqual(passenger.completion_count, 1)
        self.assertEqual(passenger.arrived_at, 16)
        self.assertTrue(all(p.board_count == p.completion_count == 1 for p in sim.passengers))

    def test_v2_designated_burst_ids_survive_concentration(self):
        rows = designated_burst_day(65001)
        designated = [row for row in rows if row[3].startswith("burst-")]
        self.assertEqual(len(rows), 120)
        self.assertEqual(len({row[3] for row in rows}), 120)
        self.assertEqual({row[3] for row in designated},
                         {f"burst-{i}" for i in range(30)})
        self.assertTrue(all(10 <= row[0] < 20 for row in designated))
        self.assertEqual({row[3]: row[1] for row in designated},
                         {f"burst-{i}": i % 3 for i in range(30)})
        validate_v2_envelope([row[:3] for row in rows])
        collided = designated_burst_day(65001, collide=True)
        self.assertEqual(len(collided), 120)
        self.assertIn((10, 29, 0, "aaa-incidental-collision"), collided)
        collision_window = [row for row in collided if 10 <= row[0] < 20]
        old_first_thirty = sorted(collision_window, key=lambda row: (row[0], row[3]))[:30]
        self.assertTrue(any(row[3] == "aaa-incidental-collision" for row in old_first_thirty))
        self.assertEqual(sum(row[3].startswith("burst-") for row in old_first_thirty), 29)
        self.assertEqual({row[3] for row in collided if row[3].startswith("burst-")},
                         {f"burst-{i}" for i in range(30)})
        validate_v2_envelope([row[:3] for row in collided])

    def test_v2_cross_owner_open_and_post_step_callbacks_survive(self):
        d = Dispatcher(30, 2)
        d.on_call(0, 5, "up")
        # Pin the legitimate pre-existing assignment: car 0 is one floor away
        # and car 1's own stop opens at the hall floor this tick.
        d._owners[5] = 0
        d.on_car_request(0, 1, 5)
        d.on_car_request(0, 0, 8)
        # The opener differs from the owner; the opening must clear shared hall work.
        self.assertEqual(d.step(0, [3, 5]), ["up", "open"])
        self.assertNotIn(5, d._hall)
        self.assertEqual(d._car_stops[0], {8: 1})
        # These callbacks arrive after the opening decision and remain live.
        d.on_call(1, 12, "down")
        d.on_car_request(1, 0, 9)
        self.assertIn(12, d._hall)
        self.assertEqual(d._car_stops[0], {8: 1, 9: 1})
        commands = d.step(1, [4, 5])
        self.assertEqual(len(commands), 2)
        self.assertIn(12, d._owners)
        self.assertEqual(d._car_stops[0], {8: 1, 9: 1})
        # Both callbacks remain serviceable after the earlier opening batch.
        trace = ([5, 5], [6, 6], [7, 7], [8, 8], [8, 9], [9, 10],
                 [9, 11], [9, 12])
        for t, positions in enumerate(trace, 2):
            commands = d.step(t, list(positions))
            self.assertEqual(len(commands), 2)
            self.assertTrue(all(c in {"up", "down", "stay", "open"} for c in commands))
        self.assertNotIn(12, d._hall)
        self.assertNotIn(12, d._owners)
        self.assertNotIn(9, d._car_stops[0])

    def test_v2_sustained_arrivals_drain_with_unique_live_hall_owners(self):
        specs = [(t, (t // 7) % 27, 29 - ((t // 11) % 27))
                 for t in (0, 7, 14, 21, 28, 35, 42, 49, 56, 63, 70, 77)]
        sim = FleetSimulation(specs, 3, [0, 14, 29])
        observations = 0
        idle_nonowner_stays = 0
        original_step = sim.dispatcher.step

        def observed_step(t, positions):
            nonlocal idle_nonowner_stays
            commands = original_step(t, positions)
            d = sim.dispatcher
            for car, command in enumerate(commands):
                has_hall_work = car in d._owners.values()
                has_car_work = bool(d._car_stops[car])
                if command == "stay" and not has_hall_work and not has_car_work:
                    idle_nonowner_stays += 1
            return commands

        sim.dispatcher.step = observed_step
        for t in range(700):
            sim.tick(t)
            d = sim.dispatcher
            self.assertTrue(set(d._owners).issubset(d._hall),
                            f"stale owner at tick {t}: {d._owners}, hall={d._hall}")
            self.assertTrue(all(0 <= owner < 3 for owner in d._owners.values()))
            observations += len(d._hall)
            if all(p.arrived_at is not None for p in sim.passengers):
                break
        self.assertTrue(all(p.arrived_at is not None for p in sim.passengers),
                        "sustained-arrival trace failed to drain by tick 699")
        self.assertGreater(observations, 0)
        self.assertGreater(idle_nonowner_stays, 0,
                           "no idle nonowner stay was observed")
        self.assertTrue(all(p.board_count == p.completion_count == 1
                            for p in sim.passengers))

    def test_fleet_initial_positions_riders_and_boarding_orders(self):
        modest_max = (0, None, None)
        for order in ("ascending", "reverse"):
            # Each car's initial rider is charged from t=0 and served by that car.
            sim = FleetSimulation([], 3, [0, 14, 29], [[2], [16], [27]], order)
            sim.run(100)
            slowest = max(sim.passengers, key=lambda p: p.arrived_at - p.called_at)
            modest_max = max(modest_max, (slowest.arrived_at - slowest.called_at,
                                          order, slowest), key=lambda x: x[0])
            self.assertEqual(len(sim.passengers), 3)
            self.assertTrue(all(p.arrived_at is not None for p in sim.passengers))
            self.assertTrue(all(sum(p in car for car in sim.cars) == 0
                                for p in sim.passengers))
            # Both cars are forced to open together at one floor. Their
            # destination-at-current-floor riders create the opening stops;
            # a shared 15-person queue must be boarded without loss.
            specs = [(0, 10, 2)] * 15
            sim = FleetSimulation(specs, 3, [10, 10, 29],
                                  [[10], [10], []], opening_order=order)
            sim.tick(0)
            self.assertEqual(sim.last_commands[:2], ["open", "open"])
            sim.run(100)
            self.assertTrue(all(p.arrived_at is not None for p in sim.passengers))
            self.assertEqual(len(sim.passengers), len(specs) + 2)
        p = modest_max[2]
        print(f"v2 modest initial load: both orders pass; worst={modest_max[0]}s order={modest_max[1]} "
              f"passenger=({p.origin}->{p.destination}, call={p.called_at}, arrival={p.arrived_at}); "
              f"unfinished=0")

    def test_v2_full_initial_load_all_cars_both_boarding_orders(self):
        maxima = []
        for order in ("ascending", "reverse"):
            riders = [[5] * CAPACITY, [10] * CAPACITY, [24] * CAPACITY]
            sim = FleetSimulation([], 3, [0, 15, 29], riders, order)
            sim.run(150)
            elapsed = max(p.arrived_at for p in sim.passengers)
            maxima.append((elapsed, order, max(sim.passengers,
                          key=lambda p: p.arrived_at)))
            self.assertEqual(len(sim.passengers), 30)
            self.assertTrue(all(p.board_count == p.completion_count == 1
                                for p in sim.passengers))
        worst = max(maxima, key=lambda row: row[0])
        p = worst[2]
        print(f"v2 full initial load: both orders pass; worst={worst[0]}s order={worst[1]} "
              f"passenger=({p.origin}->{p.destination}, call={p.called_at}, arrival={p.arrived_at}); "
              f"margin={V2_LIMIT-worst[0]}s; unfinished=0")

    def test_v2_tick_then_run_delivers_t0_and_later_arrivals_once(self):
        specs = [(0, 0, 2), (4, 20, 19)]
        sim = FleetSimulation(specs, 3, [0, 14, 29])
        sim.tick(0)
        self.assertEqual(sim.next_tick, 1)
        sim.run(100)
        self.assertEqual(len(sim.events), 0)
        self.assertEqual(len(sim.passengers), 2)
        self.assertTrue(all(p.arrived_at is not None for p in sim.passengers))

    def test_v2_generated_families_200_days_and_v1_preserved_seeds(self):
        # 50 fixtures in each prescribed traffic family. Starts vary by seed;
        # every family includes the canonical zero and separated positions.
        families = ("ordinary", "crowd", "spread_burst", "concentrated_burst")
        worst = (0, None, None, None)
        for family_index, family in enumerate(families):
            for n in range(50):
                seed = 50000 + family_index * 1000 + n
                rng = random.Random(seed)
                crowd = family == "crowd"
                burst = family in ("spread_burst", "concentrated_burst")
                specs = random_v2_day(seed, crowd=crowd, burst=burst)
                if crowd and n % 2:
                    # Mixed destination crowd: same origin and tick, 15 riders.
                    o = specs[0][1]
                    crowd_rows = []
                    for j in range(15):
                        d = (o + 1 + j) % FLOORS
                        crowd_rows.append((0, o, d))
                    specs = crowd_rows + [row for row in specs if row[0] != 0]
                    validate_v2_envelope(specs)
                if family == "concentrated_burst":
                    # Stable IDs distinguish the thirty designated riders from
                    # incidental arrivals in the same ten-second window.
                    tagged = designated_burst_day(seed)
                    designated = [row for row in tagged if row[3].startswith("burst-")]
                    self.assertEqual(len(designated), 30)
                    self.assertEqual(len({row[3] for row in designated}), 30)
                    self.assertTrue(all(10 <= row[0] < 20 for row in designated))
                    self.assertEqual({row[3]: row[1] for row in designated},
                                     {f"burst-{i}": i % 3 for i in range(30)})
                    specs = [row[:3] for row in tagged]
                    validate_v2_envelope(specs)
                if n == 0: starts = [0, 0, 0]
                elif n == 1: starts = [0, 14, 29]
                else: starts = [rng.randrange(FLOORS) for _ in range(3)]
                sim = FleetSimulation(specs, 3, starts)
                sim.run()
                elapsed = max(p.arrived_at - p.called_at for p in sim.passengers)
                slowest = max(sim.passengers,
                              key=lambda p: p.arrived_at - p.called_at)
                if elapsed > worst[0]:
                    worst = (elapsed, seed, (family, starts), slowest)
                self.assertLessEqual(elapsed, V2_LIMIT,
                                     f"family={family} seed={seed} starts={starts} worst={elapsed}")
        self.assertEqual(len(families) * 50, 200)
        self.assertLessEqual(worst[0], V2_LIMIT,
                             f"200-day worst={worst[0]} seed={worst[1]} fixture={worst[2]}")
        print(f"v2 expanded sample: 200 days; worst={worst[0]}s seed={worst[1]} "
              f"fixture={worst[2]} passenger=({worst[3].origin}->{worst[3].destination}, "
              f"call={worst[3].called_at}, arrival={worst[3].arrived_at}); "
              f"margin={V2_LIMIT-worst[0]}s")


if __name__ == "__main__":
    unittest.main()
