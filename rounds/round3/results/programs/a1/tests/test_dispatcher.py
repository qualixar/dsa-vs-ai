import random
import unittest

from dispatcher import Dispatcher


class World:
    """Small building simulator with event-before-step tick ordering."""

    def __init__(self, dispatcher, floors=30, capacity=10, positions=None):
        self.d = dispatcher
        self.floors = floors
        self.capacity = capacity
        self.pos = list(positions) if positions is not None else [0] * dispatcher.lifts
        if len(self.pos) != dispatcher.lifts:
            raise ValueError("one initial position per lift is required")
        self.riders = [[] for _ in range(dispatcher.lifts)]
        self.waiting = {}
        self.done = []
        self.events = {}
        self.opened_at = set()
        self.openings = []
        self.fire_commands = []
        self.fire_openings = []
        self.fire_arrivals = []
        self.maintenance_observations = []
        self.onboard_at_fire = []
        self.survivors_at_restoration = []
        self.maintenance_requeues = []
        self.maintenance = {}
        self._available = [True] * dispatcher.lifts
        self.modes = {}
        self.mode = "normal"
        self.evacuated = []
        self.fire_deadlines = [None] * dispatcher.lifts
        self.registry = {}
        self.pressure_observations = []
        self.lobby_pressure_observations = []
        self.boardings = []
        self.loaded_moves = []

    def register(self, p):
        if "id" not in p:
            p["id"] = len(self.registry)
        if p["id"] in self.registry:
            raise AssertionError(("duplicate passenger id", p["id"]))
        self.registry[p["id"]] = p

    def arrival(self, t, origin, dest):
        p = {"origin": origin, "dest": dest, "start": t}
        self.register(p)
        self.events.setdefault(t, []).append((origin, dest, p))

    def set_lift_available(self, t, lift, available):
        self.maintenance.setdefault(t, []).append((lift, available))

    def set_mode(self, t, mode):
        self.modes.setdefault(t, []).append(mode)

    def tick(self, t):
        # Tests may seed riders already aboard to model a building startup.
        # Register those initial passengers before processing this tick.
        for group in [*self.riders, *self.waiting.values(),
                      [p for p, _ in self.done], self.evacuated]:
            for p in group:
                if "id" not in p:
                    self.register(p)
        for mode in self.modes.pop(t, []):
            previous = self.mode
            self.mode = mode
            self.d.set_mode(t, mode)
            if mode == "fire" and previous != "fire":
                self.onboard_at_fire.extend((t, lift, p["id"]) for lift, riders in enumerate(self.riders) for p in riders)
                self.fire_deadlines = [t + self.floors + 2 if self.available(i) else None
                                       for i in range(self.d.lifts)]
            if mode == "normal":
                self.survivors_at_restoration.extend((t, lift, p["id"]) for lift, riders in enumerate(self.riders) for p in riders)
                # Waiting passengers remain in place throughout fire mode.
                for floor, people in self.waiting.items():
                    for p in people:
                        self.d.on_call(t, floor, "up" if p["dest"] > floor else "down")
        for lift, available in self.maintenance.pop(t, []):
            was_available = self.available(lift)
            self._available[lift] = available
            self.d.set_lift_available(t, lift, available)
            if available and not was_available and self.mode == "fire":
                self.fire_deadlines[lift] = t + self.floors + 2
            if not available:
                floor = self.pos[lift]
                self.maintenance_observations.append((t, lift, available, floor))
                for p in self.riders[lift]:
                    if p["dest"] == floor:
                        self.done.append((p, t))
                    else:
                        self.waiting.setdefault(floor, []).append(p)
                        self.maintenance_requeues.append((t, lift, floor, p["id"]))
                        self.d.on_call(t, floor, "up" if p["dest"] > floor else "down")
                self.riders[lift] = []
            else:
                self.maintenance_observations.append((t, lift, available, self.pos[lift]))
        for origin, dest, p in self.events.pop(t, []):
            self.waiting.setdefault(origin, []).append(p)
            direction = "up" if dest > origin else "down"
            self.d.on_call(t, origin, direction)
        cmd = self.d.step(t, list(self.pos))
        if len(cmd) != len(self.pos) or any(c not in ("up", "down", "stay", "open") for c in cmd):
            raise AssertionError((t, cmd))
        for lift, command in enumerate(cmd):
            if not self.available(lift) and command != "stay":
                raise AssertionError((t, "unavailable lift did not stay", lift, command))
        if self.mode == "fire":
            for lift, command in enumerate(cmd):
                at = self.pos[lift]
                self.fire_commands.append((t, lift, at, command))
                if not self.available(lift):
                    self.assert_command(command == "stay", (t, "unavailable moved", lift, command))
                elif t >= self.fire_deadlines[lift]:
                    self.assert_command(at == 0 and command == "open",
                                        (t, "missed recall deadline", lift, at, command,
                                         self.fire_deadlines[lift]))
                if command == "up" or (command == "open" and at != 0):
                    raise AssertionError((t, "invalid fire command", lift, at, command))
                if command == "down":
                    if at == 0:
                        raise AssertionError((t, "down below zero", at))
                    self.pos[lift] -= 1
                    if self.pos[lift] == 0:
                        self.fire_arrivals.append((t, lift, 0))
                elif command == "open" and at == 0:
                    self.fire_openings.append((t, lift, at, tuple(p["id"] for p in self.riders[lift])))
                    self.evacuated.extend(self.riders[lift])
                    self.riders[lift] = []
            self.assert_conserved()
            return
        # Apply lifts in index order. Shared waiting queues mean a passenger
        # can board only once even when multiple lifts open on the same floor.
        for lift, c in enumerate(cmd):
            at = self.pos[lift]
            if c in ("up", "down"):
                for p in self.riders[lift]:
                    self.loaded_moves.append((t, lift, at, c, p["id"]))
            if c == "up":
                if at >= self.floors - 1:
                    raise AssertionError((t, "up beyond top", at))
                self.pos[lift] += 1
            elif c == "down":
                if at <= 0:
                    raise AssertionError((t, "down below zero", at))
                self.pos[lift] -= 1
            elif c == "open":
                if self.mode == "fire" and at == 0:
                    self.fire_arrivals.append((t, lift, at))
                self.opened_at.add(at)
                self.openings.append((t, lift, at))
                keep = []
                for p in self.riders[lift]:
                    if p["dest"] == at:
                        self.done.append((p, t))
                    else:
                        keep.append(p)
                self.riders[lift] = keep
                people = self.waiting.get(at, [])
                room = self.capacity - len(keep)
                boarded, remain = people[:room], people[room:]
                self.riders[lift].extend(boarded)
                self.waiting[at] = remain
                for p in boarded:
                    self.boardings.append((t, lift, at, p["id"]))
                    self.d.on_car_request(t, lift, p["dest"])
                if remain:
                    # Left-behind passengers retain their original start time.
                    for p in remain:
                        self.d.on_call(t, at, "up" if p["dest"] > at else "down")
        self.assert_conserved()
        self.pressure_observations.append((t, sum(map(len, self.waiting.values())),
                                           sum(map(len, self.riders))))
        self.lobby_pressure_observations.append((t, len(self.waiting.get(0, ())),
                                                  sum(map(len, self.riders))))

    def assert_conserved(self):
        locations = {}
        for events in self.events.values():
            for _, _, p in events:
                locations.setdefault(p["id"], []).append("future")
        for people in self.waiting.values():
            for p in people:
                locations.setdefault(p["id"], []).append("waiting")
        for lift_riders in self.riders:
            for p in lift_riders:
                locations.setdefault(p["id"], []).append("onboard")
        for p, _ in self.done:
            locations.setdefault(p["id"], []).append("done")
        for p in self.evacuated:
            locations.setdefault(p["id"], []).append("evacuated")
        if set(locations) != set(self.registry):
            raise AssertionError(("passenger conservation", set(locations), set(self.registry)))
        if not all(len(v) == 1 for v in locations.values()):
            raise AssertionError(("passenger appears in multiple states", locations))

    def run(self, last_tick, cutoff=3000):
        for t in range(last_tick + 1):
            self.tick(t)
        t = last_tick + 1
        while t < cutoff and (self.events or self.modes or self.maintenance
                               or any(self.waiting.values()) or any(self.riders)):
            self.tick(t)
            t += 1
        if self.events or self.modes or self.maintenance or any(self.waiting.values()) or any(self.riders):
            raise AssertionError(("world did not drain", t, self.events, self.modes,
                                  self.maintenance, self.waiting, self.riders))
        self.assert_conserved()
        return t

    def available(self, lift):
        # Simulator-owned physical state, independent of dispatcher internals.
        return self._available[lift]

    @staticmethod
    def assert_command(condition, detail):
        if not condition:
            raise AssertionError(detail)


class DispatcherContractTests(unittest.TestCase):
    def test_idle_and_car_only_initial_rider(self):
        d = Dispatcher(30, 1)
        self.assertEqual(d.step(0, [12]), ["stay"])
        d.on_car_request(0, 0, 13)
        w = World(d)
        w.pos = [12]
        w.riders[0] = [{"origin": 12, "dest": 13, "start": 0}]
        w.run(0, 20)
        self.assertEqual(len(w.done), 1)
        self.assertLessEqual(w.done[0][1], 3)

    def test_invalid_inputs_fail_safe(self):
        d = Dispatcher(30, 2)
        for args in [(0, -1, "up"), (0, 30, "down"), (0, 3, "side"), (0, True, "up")]:
            d.on_call(*args)
        for args in [(0, -1, 2), (0, 4, 2), (0, True, 1)]:
            d.on_car_request(*args)
        self.assertEqual(d.step(0, [1]), ["stay", "stay"])
        self.assertEqual(d.step(0, [1, 30]), ["stay", "stay"])
        self.assertEqual(d.step(0, [1, 2]), ["stay", "stay"])

    def test_hall_both_directions_duplicates_reversals_and_reopen(self):
        d = Dispatcher(6, 1)
        d.on_call(0, 4, "up")
        d.on_call(0, 4, "down")
        d.on_call(1, 4, "up")
        pos = 0
        commands = []
        for t in range(20):
            c = d.step(t, [pos])[0]
            commands.append((pos, c))
            if c == "up": pos += 1
            elif c == "down": pos -= 1
        self.assertEqual(commands.count((4, "open")), 1)
        # A fresh press after the opening is serviceable.
        d.on_call(21, 4, "down")
        self.assertEqual(d.step(21, [4]), ["open"])

    def test_simultaneous_car_destinations_complete(self):
        d = Dispatcher(8, 1)
        d.on_car_request(0, 0, 2)
        d.on_car_request(0, 0, 6)
        w = World(d, floors=8)
        w.pos = [0]
        w.riders[0] = [
            {"origin": 0, "dest": 2, "start": 0},
            {"origin": 0, "dest": 6, "start": 0},
        ]
        w.run(0, 30)
        self.assertEqual({p["dest"] for p, _ in w.done}, {2, 6})

    def test_capacity_repress_and_wait_time_not_reset(self):
        d = Dispatcher(30, 1)
        w = World(d)
        for _ in range(12):
            w.arrival(0, 5, 9)
        w.run(0, 100)
        self.assertEqual(len(w.done), 12)
        self.assertTrue(all(t - p["start"] < 100 for p, t in w.done))


def make_random_day(seed):
    # Regenerate a complete day rather than shifting an event: shifting can
    # silently move arrivals outside the promised first-600-tick window.
    for attempt in range(1000):
        rng = random.Random((seed, attempt).__repr__())
        sizes = [12, 12]
        remaining = 16
        while remaining:
            size = min(remaining, rng.randint(1, 5))
            sizes.append(size)
            remaining -= size
        arrivals = []
        for size in sizes:
            tick = rng.randrange(600)
            origin = rng.randrange(30)
            destinations = [rng.choice([f for f in range(30) if f != origin]) for _ in range(size)]
            arrivals.extend((tick, origin, dest) for dest in destinations)
        arrivals.sort()
        crowd = {}
        for t, origin, _ in arrivals:
            crowd[(t, origin)] = crowd.get((t, origin), 0) + 1
        if max(crowd.values()) > 12:
            continue
        if any(sum(1 for t, _, _ in arrivals if end - width + 1 <= t <= end) > cap
               for width, cap in ((10, 15), (60, 20), (300, 35))
               for end in range(600)):
            continue
        return arrivals
    raise AssertionError(f"could not generate valid day for seed {seed}")


def assert_valid_envelope(testcase, arrivals):
    testcase.assertEqual(len(arrivals), 40)
    testcase.assertTrue(all(isinstance(t, int) and 0 <= t <= 599 for t, _, _ in arrivals))
    testcase.assertTrue(all(0 <= o < 30 and 0 <= d < 30 and o != d for _, o, d in arrivals))
    crowd = {}
    for t, o, _ in arrivals:
        crowd[(t, o)] = crowd.get((t, o), 0) + 1
    testcase.assertLessEqual(max(crowd.values()), 12)
    for width, cap in ((10, 15), (60, 20), (300, 35)):
        for end in range(600):
            testcase.assertLessEqual(sum(1 for t, _, _ in arrivals if end - width + 1 <= t <= end), cap)


class VersionOneTrafficTests(unittest.TestCase):
    def test_seed_19_overflow_regression(self):
        arrivals = make_random_day(19)
        assert_valid_envelope(self, arrivals)
        self.assertEqual(arrivals, make_random_day(19))

    def test_seeded_random_envelope(self):
        seeds = range(20)
        maximum = 0
        failures = []
        for seed in seeds:
            arrivals = make_random_day(seed)
            assert_valid_envelope(self, arrivals)
            crowd = {}
            w = World(Dispatcher(30, 1))
            for t, o, dest in arrivals:
                crowd[(t, o)] = crowd.get((t, o), 0) + 1
                w.arrival(t, o, dest)
            self.assertLessEqual(max(crowd.values()), 12)
            self.assertTrue(any(size >= 11 for size in crowd.values()))
            w.run(599, 2500)
            if len(w.done) != 40:
                failures.append((seed, "incomplete", len(w.done)))
                continue
            waits = [t - p["start"] for p, t in w.done]
            maximum = max(maximum, max(waits))
            if max(waits) > 270:
                failures.append((seed, max(waits), [(p["start"], p["origin"], p["dest"], t)
                                                    for p, t in w.done if t - p["start"] > 270]))
        self.assertFalse(failures, f"20-day sample max wait={maximum}; failures={failures!r}")


def make_v2_day(seed):
    """120 arrivals with a 15-person crowd and a 30-person ten-tick burst."""
    for attempt in range(5000):
        rng = random.Random(f"v2:{seed}:{attempt}")
        arrivals = [(100, 8, rng.choice([f for f in range(30) if f != 8]))
                    for _ in range(15)]
        arrivals.extend((200 + i % 10, rng.randrange(30), 0) for i in range(30))
        # Replace any accidental same-floor destinations in the burst.
        arrivals = [(t, o, d if d != o else (d + 1) % 30) for t, o, d in arrivals]
        for _ in range(75):
            t = rng.randrange(600)
            # Keep the deliberately dense features interpretable and valid.
            while 90 <= t <= 110 or 190 <= t <= 220:
                t = rng.randrange(600)
            o = rng.randrange(30)
            d = rng.choice([f for f in range(30) if f != o])
            arrivals.append((t, o, d))
        arrivals.sort()
        try:
            assert_valid_v2_envelope(unittest.TestCase(), arrivals)
        except AssertionError:
            continue
        return arrivals
    raise AssertionError(f"could not generate valid v2 day for seed {seed}")


def assert_valid_v2_envelope(testcase, arrivals):
    testcase.assertEqual(len(arrivals), 120)
    testcase.assertTrue(all(isinstance(t, int) and 0 <= t <= 599 for t, _, _ in arrivals))
    testcase.assertTrue(all(0 <= o < 30 and 0 <= d < 30 and o != d for _, o, d in arrivals))
    crowd = {}
    by_tick = {}
    for t, o, _ in arrivals:
        crowd[(t, o)] = crowd.get((t, o), 0) + 1
        by_tick[t] = by_tick.get(t, 0) + 1
    testcase.assertLessEqual(max(crowd.values()), 15)
    testcase.assertEqual(crowd.get((100, 8)), 15)
    testcase.assertEqual(sum(1 for t, _, _ in arrivals if 200 <= t < 210), 30)
    for width, cap in ((10, 35), (60, 50), (300, 90)):
        for end in range(600):
            testcase.assertLessEqual(sum(n for t, n in by_tick.items()
                                         if end - width + 1 <= t <= end), cap)


class VersionTwoTests(unittest.TestCase):
    def test_contract_and_independent_initial_riders(self):
        d = Dispatcher(8, 3)
        for lift, dest in enumerate((2, 5, 7)):
            d.on_car_request(0, lift, dest)
        w = World(d, floors=8, positions=[0, 3, 6])
        w.riders = [[{"origin": p, "dest": dest, "start": 0}]
                    for p, dest in zip(w.pos, (2, 5, 7))]
        w.run(0, 60)
        self.assertEqual(len(w.done), 3)

    def test_shared_queue_simultaneous_open_and_boundary_safety(self):
        d = Dispatcher(6, 3)
        d.on_call(0, 0, "up")
        w = World(d, floors=6, positions=[0, 0, 5])
        w.arrival(0, 0, 4)
        w.tick(0)
        # Two cars at the same floor must not both claim the hall stop.
        self.assertEqual(sum(1 for _, _, floor in w.openings if floor == 0), 1)
        self.assertEqual(sum(len(r) for r in w.riders), 1)
        edge = Dispatcher(6, 3)
        edge.on_call(0, 5, "up")  # invalid edge call is ignored
        self.assertEqual(edge.step(0, [0, 5, 2]), ["stay", "stay", "stay"])
        self.assertEqual(edge.step(1, [-1, 5, 2]), ["stay", "stay", "stay"])

    def test_seeded_v2_days(self):
        maximum = 0
        failures = []
        for seed in range(20):
            arrivals = make_v2_day(seed)
            assert_valid_v2_envelope(self, arrivals)
            w = World(Dispatcher(30, 3))
            for t, origin, dest in arrivals:
                w.arrival(t, origin, dest)
            w.run(599, 3000)
            if len(w.done) != 120:
                failures.append((seed, "incomplete", len(w.done)))
                continue
            waits = [t - p["start"] for p, t in w.done]
            maximum = max(maximum, max(waits))
            if max(waits) > 290:
                failures.append((seed, max(waits), [(p["start"], p["origin"], p["dest"], t)
                                                    for p, t in w.done if t-p["start"] > 290]))
        self.assertFalse(failures, f"20 v2 days max wait={maximum}; failures={failures!r}")


def make_v5_day(seed):
    """Make a reproducible, validity-filtered rush with varied arrival times."""
    rng = random.Random(f"v5:{seed}")
    arrivals = []
    # Six-person lobby groups retain envelope headroom; seed-dependent jitter
    # changes the timetable while preserving the concentrated morning load.
    for group in range(40):
        t = group * 7 + ((group * seed) % 3 if seed else 0)
        arrivals.extend((t, 0, rng.randrange(1, 30)) for _ in range(6))
    for group in range(10):
        t = group * 29 + 3 + ((group * seed) % 3 if seed else 0)
        origin = rng.randrange(1, 30)
        for _ in range(6):
            dest = rng.randrange(30)
            while dest == origin:
                dest = rng.randrange(30)
            arrivals.append((t, origin, dest))
    arrivals.sort()
    assert_valid_v5_envelope(unittest.TestCase(), arrivals)
    return arrivals


def make_v5_legacy_day(seed):
    """Original unjittered timetable, retained as a named regression family."""
    rng = random.Random(f"v5:{seed}")
    arrivals = []
    for group in range(40):
        arrivals.extend((group * 7, 0, rng.randrange(1, 30)) for _ in range(6))
    for group in range(10):
        origin = rng.randrange(1, 30)
        for _ in range(6):
            dest = rng.randrange(30)
            while dest == origin:
                dest = rng.randrange(30)
            arrivals.append((group * 29 + 3, origin, dest))
    arrivals.sort()
    assert_valid_v5_envelope(unittest.TestCase(), arrivals)
    return arrivals


def make_v5_spread_day(seed):
    """Dispersed 1–4 person groups and upstairs starts, filtered only by validity."""
    rng = random.Random(f"v5-spread:{seed}")
    for attempt in range(1000):
        lobby_sizes = [1] * 60 + [2] * 40 + [3] * 20 + [4] * 10  # 240
        rng.shuffle(lobby_sizes)
        upper_sizes = [1] * 30 + [2] * 15  # 60
        rng.shuffle(upper_sizes)
        arrivals = []
        for i, size in enumerate(lobby_sizes):
            t = i * 2
            arrivals.extend((t, 0, rng.choice(range(1, 30))) for _ in range(size))
        for i, size in enumerate(upper_sizes):
            t = i * 5
            origin = rng.randrange(1, 30)
            for _ in range(size):
                dest = rng.randrange(30)
                while dest == origin: dest = rng.randrange(30)
                arrivals.append((t, origin, dest))
        arrivals.sort()
        try:
            assert_valid_v5_envelope(unittest.TestCase(), arrivals)
            return arrivals
        except AssertionError:
            continue
    raise AssertionError(f"could not generate valid spread day {seed}")


def make_v5_clustered_day(seed):
    """Six-person crowds and localized concurrent lobby/upstairs demand."""
    rng = random.Random(f"v5-cluster:{seed}")
    for attempt in range(1000):
        arrivals = []
        # 40 lobby clusters, each six riders, separated enough for rolling caps.
        for i in range(40):
            t = i * 7 + rng.randrange(2)
            arrivals.extend((t, 0, rng.choice((1, 2, 28, 29))) for _ in range(6))
        # Ten six-person upstairs clusters, synchronized with selected lobby groups.
        for i in range(10):
            t = i * 28 + rng.randrange(2)
            origin = rng.choice((1, 2, 28, 29))
            for _ in range(6):
                dest = rng.choice((0, 1, 2, 28, 29))
                while dest == origin: dest = rng.choice((0, 1, 2, 28, 29))
                arrivals.append((t, origin, dest))
        arrivals.sort()
        try:
            assert_valid_v5_envelope(unittest.TestCase(), arrivals)
            return arrivals
        except AssertionError:
            continue
    raise AssertionError(f"could not generate valid clustered day {seed}")


def v5_manifest():
    return ([ ("current", seed, make_v5_day(seed)) for seed in range(20) ] +
            [("legacy", seed, make_v5_legacy_day(seed)) for seed in range(5)] +
            [("spread", seed, make_v5_spread_day(seed)) for seed in range(100, 110)] +
            [("clustered", seed, make_v5_clustered_day(seed)) for seed in range(200, 210)])


def assert_valid_v5_envelope(testcase, arrivals):
    testcase.assertEqual(len(arrivals), 300)
    testcase.assertEqual(sum(origin == 0 for _, origin, _ in arrivals), 240)
    testcase.assertEqual(sum(origin != 0 for _, origin, _ in arrivals), 60)
    testcase.assertTrue(all(type(t) is int and type(origin) is int and type(dest) is int and
                            0 <= t < 300 and 0 <= origin < 30 and
                            0 <= dest < 30 and origin != dest
                            for t, origin, dest in arrivals))
    crowd = {}
    for t, origin, _ in arrivals:
        crowd[t, origin] = crowd.get((t, origin), 0) + 1
    testcase.assertLessEqual(max(crowd.values()), 6)
    for end in range(300):
        ten = [row for row in arrivals if end - 9 <= row[0] <= end]
        sixty = [row for row in arrivals if end - 59 <= row[0] <= end]
        testcase.assertLessEqual(len(ten), 25)
        testcase.assertLessEqual(len(sixty), 85)
        testcase.assertLessEqual(sum(origin != 0 for _, origin, _ in sixty), 25)


class VersionFiveMorningRushTests(unittest.TestCase):
    def test_v5_frozen_manifest_validity_and_diversity(self):
        manifest = v5_manifest()
        self.assertEqual(len(manifest), 45)
        signatures = {}
        for family, seed, arrivals in manifest:
            assert_valid_v5_envelope(self, arrivals)
            signatures.setdefault(family, set()).add(tuple(sorted(
                (t, origin, sum(1 for tt, oo, _ in arrivals if (tt, oo) == (t, origin)))
                for t, origin, _ in arrivals)))
        for family in ("spread", "clustered"):
            self.assertGreaterEqual(len(signatures[family]), 2)

    def test_v5_validator_rejects_envelope_violations(self):
        valid = make_v5_day(0)
        cases = {}

        # Each fixture changes only the named property where possible, so the
        # validator failure documents the corresponding envelope gate.
        cases["total"] = valid[:-1]
        cases["cohort"] = [(0, 1, valid[0][2]), *valid[1:]]
        cases["boolean tick"] = [(True, valid[0][1], valid[0][2]), *valid[1:]]
        # Preserve the origin cohort (`0.0 == 0`) so the strict type gate is
        # the first named rejection; likewise cover both floor fields.
        cases["fractional origin"] = [(valid[0][0], 0.0, valid[0][2]), *valid[1:]]
        cases["fractional destination"] = [(valid[0][0], valid[0][1], 1.5), *valid[1:]]
        cases["boolean origin"] = [(valid[0][0], False, valid[0][2]), *valid[1:]]
        cases["boolean destination"] = [(valid[0][0], valid[0][1], True), *valid[1:]]
        cases["negative tick"] = [(-1, valid[0][1], valid[0][2]), *valid[1:]]
        cases["tick past window"] = [(300, valid[0][1], valid[0][2]), *valid[1:]]
        cases["negative origin"] = [(valid[0][0], -1, valid[0][2]), *valid[1:]]
        cases["origin past top"] = [(valid[0][0], 30, valid[0][2]), *valid[1:]]
        cases["negative destination"] = [(valid[0][0], valid[0][1], -1), *valid[1:]]
        cases["destination past top"] = [(valid[0][0], valid[0][1], 30), *valid[1:]]
        cases["same-floor destination"] = [(valid[0][0], valid[0][1], valid[0][1]), *valid[1:]]
        cases["crowd"] = [(0, 0, 1)] * 7 + valid[7:]
        # Build cap fixtures from independently valid cohort sets. Group
        # sizes stay at or below six and destinations stay distinct.
        lobby = [(t, 0, 1 + (i % 29)) for i, t in enumerate(
            [*([0] * 6), *([1] * 5), *([2] * 5), *([3] * 5), *([4] * 5),
             *([100 + i // 6 for i in range(214)])])]
        # The first 26 lobby arrivals violate only the ten-second cap.
        cases["ten-second cap"] = lobby + [
            (150 + i // 6, 1 + (i % 29), 0) for i in range(25)] + [
            (220 + i // 6, 1 + (i % 29), 0) for i in range(25)] + [
            (290 + i // 6, 1 + (i % 29), 0) for i in range(10)]

        # Put 61 lobby and 25 upstairs arrivals in [0, 60), with at most
        # two arrivals per tick. This isolates the 86/60-second violation.
        lobby_sixty = [(i, 0, 1 + i % 29) for i in range(61)]
        lobby_sixty += [(100 + i, 0, 1 + i % 29) for i in range(179)]
        upper_sixty = [(i + 1, 1 + i % 29, 0) for i in range(25)]
        upper_sixty += [(100 + i, 1 + i % 29, 0) for i in range(35)]
        cases["sixty-second cap"] = lobby_sixty + upper_sixty

        # 26 upstairs starts in 60 seconds, distributed so no floor crowd
        # exceeds six; the total 60-second count remains below 85.
        upper_cap = [(i // 6, 1 + i % 29, 0) for i in range(26)]
        upper_cap += [(240 + i // 6, 1 + i % 29, 0) for i in range(34)]
        cases["upstairs sixty-second cap"] = (
            [(150 + i // 6, 0, 1 + i % 29) for i in range(240)] + upper_cap)
        # Precheck each fixture against all unrelated envelope properties.
        # This prevents a misleading label from passing via an earlier gate.
        for label, arrivals in cases.items():
            with self.subTest(label=label):
                self.assertEqual(len(arrivals), 300 if label != "total" else 299)
                if label not in ("cohort", "total", "negative origin", "origin past top", "crowd"):
                    self.assertEqual(sum(o == 0 for _, o, _ in arrivals), 240)
                    self.assertEqual(sum(o != 0 for _, o, _ in arrivals), 60)
                with self.assertRaises(AssertionError, msg=f"validator accepted {label} violation"):
                    assert_valid_v5_envelope(self, arrivals)

    def test_upstairs_passenger_is_served_during_lobby_backlog(self):
        # Keep a lobby queue throughout the trip while an upstairs passenger
        # calls for service. This checks the separate upstairs guarantee in
        # the same operating condition as the morning rush.
        w = World(Dispatcher(30, 3))
        for t in range(0, 240):
            for _ in range(6):
                w.arrival(t, 0, 29)
        w.arrival(25, 14, 3)
        w.arrival(35, 3, 26)
        # This is a focused routing diagnostic, not an acceptance day: its
        # deliberately sustained six-person-per-tick lobby load is far beyond
        # the v5 envelope and is not expected to drain in the simulator cutoff.
        for t in range(240):
            w.tick(t)
        upstairs = [(p, t) for p, t in w.done if p["origin"] != 0]
        self.assertEqual(len(upstairs), 2)
        self.assertEqual({p["origin"] for p, _ in upstairs}, {3, 14})
        self.assertTrue(all(completed - p["start"] <= 190 for p, completed in upstairs))
        for p, completed in upstairs:
            boarding = next(row for row in w.boardings if row[3] == p["id"])
            bt, lift, floor, _ = boarding
            self.assertEqual(floor, p["origin"])
            self.assertTrue(any(done_p["id"] == p["id"] and done_t == completed
                                for done_p, done_t in w.done))
            self.assertTrue(any(row[0] >= bt and row[1] == lift and row[4] == p["id"]
                                for row in w.loaded_moves))
            pressure = {tick: waiting for tick, waiting, _ in w.lobby_pressure_observations}
            self.assertTrue(all(pressure.get(tick, 0) > 0
                                for tick in range(p["start"], completed + 1)), p)
        pressure_by_tick = {t: waiting for t, waiting, _ in w.lobby_pressure_observations}
        self.assertTrue(all(pressure_by_tick[t] > 0 for t in range(25, 120)))

    def test_overflow_ids_board_on_later_departures_and_complete_once(self):
        w = World(Dispatcher(8, 3), floors=8)
        for _ in range(15):
            w.arrival(0, 0, 7)
        w.run(0, 100)
        self.assertEqual(len(w.done), 15)
        completed_ids = [p["id"] for p, _ in w.done]
        self.assertEqual(len(set(completed_ids)), 15)
        boarded = [pid for _, _, floor, pid in w.boardings if floor == 0]
        self.assertEqual(len(boarded), 15)
        self.assertEqual(len(set(boarded)), 15)
        departure_ids = {pid for _, _, _, direction, pid in w.loaded_moves
                         if direction == "up"}
        self.assertEqual(set(completed_ids), departure_ids)
        lobby_departures = [t for t, _, floor in w.openings if floor == 0]
        self.assertGreaterEqual(len(lobby_departures), 2)

    def test_v5_seeded_morning_rush(self):
        # Acceptance is statistical for lobby riders: nearest-rank p95 over
        # all lobby riders must meet the limit. Upstairs riders and everyone
        # overall have individual limits.
        for family, seed, arrivals in v5_manifest():
            assert_valid_v5_envelope(self, arrivals)
            w = World(Dispatcher(30, 3))
            for t, origin, dest in arrivals:
                w.arrival(t, origin, dest)
            w.run(299, 3000)
            self.assertEqual(len(w.done), 300, (family, seed, len(w.done)))
            lobby = sorted(t - p["start"] for p, t in w.done if p["origin"] == 0)
            upstairs = [t - p["start"] for p, t in w.done if p["origin"] != 0]
            all_waits = [t - p["start"] for p, t in w.done]
            p95 = lobby[(95 * len(lobby) + 99) // 100 - 1]
            self.assertLessEqual(p95, 1760, (family, seed, p95))
            self.assertLessEqual(max(upstairs), 190, (family, seed, max(upstairs)))
            self.assertLessEqual(max(all_waits), 1850, (family, seed, max(all_waits)))


class VersionThreeMaintenanceTests(unittest.TestCase):
    def test_out_of_service_stays_and_return_preserves_calls(self):
        d = Dispatcher(8, 3)
        d.on_call(0, 7, "down")
        d.set_lift_available(1, 0, False)
        self.assertEqual(d.step(1, [0, 2, 4])[0], "stay")
        d.set_lift_available(2, 0, True)
        positions = [0, 2, 4]
        served = False
        for t in range(2, 30):
            commands = d.step(t, positions)
            self.assertEqual(len(commands), 3)
            for i, command in enumerate(commands):
                if command == "open" and positions[i] == 7:
                    served = True
                elif command == "up":
                    positions[i] += 1
                elif command == "down":
                    positions[i] -= 1
        self.assertTrue(served)

    def test_withdrawal_evicts_riders_and_other_lifts_finish_trip(self):
        d = Dispatcher(10, 3)
        w = World(d, floors=10, positions=[4, 0, 9])
        # Lift 0 has a rider whose request is known to the dispatcher.
        d.on_car_request(0, 0, 8)
        w.riders[0] = [{"origin": 1, "dest": 8, "start": 0}]
        w.set_lift_available(1, 0, False)
        w.set_lift_available(20, 0, True)
        w.run(20, 200)
        self.assertEqual(len(w.done), 1)
        self.assertLessEqual(w.done[0][1], 100)
        self.assertEqual(w.riders[0], [])

    def test_invalid_maintenance_inputs_are_safe(self):
        d = Dispatcher(6, 3)
        for args in [(0, -1, False), (0, 3, False), (0, True, False), (0, 1, 0)]:
            d.set_lift_available(*args)
        self.assertEqual(d.step(0, [0, 2, 5]), ["stay"] * 3)

    def test_seeded_v3_days_with_permanent_and_temporary_outage(self):
        failures = []
        maximum = 0
        for seed in range(5):
            w = World(Dispatcher(30, 3))
            for t, origin, dest in make_v2_day(100 + seed):
                w.arrival(t, origin, dest)
            # One car is out from the first tick; a second is out for 120 s.
            w.set_lift_available(0, 0, False)
            w.set_lift_available(100, 1, False)
            w.set_lift_available(220, 1, True)
            w.run(599, 3000)
            if len(w.done) != 120:
                failures.append((seed, "incomplete", len(w.done)))
                continue
            waits = [t - p["start"] for p, t in w.done]
            maximum = max(maximum, max(waits))
            if max(waits) > 510:
                failures.append((seed, max(waits)))
        self.assertFalse(failures, f"5 v3 days max wait={maximum}; failures={failures!r}")


class VersionFourFireTests(unittest.TestCase):
    matrix_metrics = []

    def test_v4_eighty_day_traffic_matrix_with_identity_accounting(self):
        summaries = []
        for family, seed_base in enumerate((1000, 2000, 3000, 4000)):
            for offset in range(20):
                seed = seed_base + offset
                arrivals = make_v2_day(seed)
                assert_valid_v2_envelope(self, arrivals)
                start = 60 + (offset * 19 + family * 31) % 420
                duration = 10 + (offset * 17 + family * 23) % 111
                end = start + duration
                outages = []
                if family == 1:
                    outages = [(0, offset % 3, False)]
                elif family == 2:
                    permanent = offset % 3
                    temporary = (permanent + 1 + offset % 2) % 3
                    # A long fire leaves enough time to observe this return's
                    # own recall deadline, even after the global deadline.
                    duration = 100 + offset % 21
                    end = start + duration
                    outages = [(0, permanent, False), (start + 5, temporary, False),
                               (start + 35, temporary, True)]
                elif family == 3:
                    first, second = offset % 3, (offset + 1) % 3
                    outages = [(start - 10, first, False), (start + 5, second, False),
                               (start + 35, second, True), (start + 50, first, True)]

                # Validate the design schedule independently of dispatch.
                self.assertTrue(60 <= start <= 479)
                self.assertTrue(10 <= end - start <= 120)
                state = [True] * 3
                histories = [[] for _ in range(3)]
                for t, lift, available in outages:
                    self.assertFalse(any(not x for x in state) and not available
                                     and sum(not x for x in state) >= 2)
                    self.assertTrue(state[lift] != available)
                    state[lift] = available
                    histories[lift].append((t, available))
                self.assertLessEqual(sum(1 for h in histories if h), 2)
                self.assertTrue(all(len(h) <= 2 for h in histories))
                # Two unavailable lifts may overlap for at most 120 ticks.
                two_out_ticks = 0
                for t in range(600):
                    active = [True] * 3
                    for event_t, lift, available in outages:
                        if event_t <= t:
                            active[lift] = available
                    self.assertGreaterEqual(sum(active), 1)
                    if sum(active) == 1:
                        two_out_ticks += 1
                self.assertLessEqual(two_out_ticks, 120)

                w = World(Dispatcher(30, 3))
                for t, origin, dest in arrivals:
                    w.arrival(t, origin, dest)
                for t, lift, available in outages:
                    w.set_lift_available(t, lift, available)
                w.set_mode(start, "fire")
                w.set_mode(end, "normal")
                w.run(599, 3000)
                self.assertEqual(len(w.registry), 120)
                self.assertEqual(len(w.done) + len(w.evacuated), 120)
                waits = [t - p["start"] for p, t in w.done]
                maximum = max(waits, default=None)
                self.assertTrue(all(wait <= 590 for wait in waits),
                                (family, seed, start, end, outages, maximum))
                observed_returns = tuple((t, lift, floor) for t, lift, available, floor
                                         in w.maintenance_observations if available)
                interactions = {
                    "onboard_at_fire": tuple(w.onboard_at_fire),
                    "fire_openings": tuple(w.fire_openings),
                    "fire_arrivals": tuple(w.fire_arrivals),
                    "survivors_at_restoration": tuple(w.survivors_at_restoration),
                    "maintenance_requeues": tuple(w.maintenance_requeues),
                }
                summaries.append((family, seed, len(w.done), len(w.evacuated), maximum,
                                  start, end, tuple(outages), observed_returns,
                                  len(w.registry), 0, 0, 0, interactions))
        self.assertEqual(len(summaries), 80)
        type(self).matrix_metrics = summaries

    def test_design_boundary_fire_intervals(self):
        # The design permits both endpoint starts and durations. Verify the
        # end tick is normal again and the final fire tick still commands open.
        for start, duration in ((60, 10), (60, 120), (479, 10), (479, 120)):
            d = Dispatcher(3, 1)
            for t in range(start):
                d.step(t, [0])
            d.set_mode(start, "fire")
            for t in range(start, start + duration):
                self.assertEqual(d.step(t, [0]), ["open"], (start, duration, t))
            d.set_mode(start + duration, "normal")
            self.assertEqual(d.step(start + duration, [0]), ["stay"], (start, duration))

    def test_fire_ending_at_tick_599_is_active_through_tick_598(self):
        d = Dispatcher(3, 1)
        for t in range(479):
            d.step(t, [0])
        d.set_mode(479, "fire")
        self.assertEqual(d.step(598, [0]), ["open"])
        d.set_mode(599, "normal")
        self.assertEqual(d.step(599, [0]), ["stay"])

    def test_fire_boundary_callbacks_are_order_independent_for_lift_state(self):
        # Both callbacks are delivered before step. A returning lift must be
        # available for the fire override regardless of callback order.
        for order in (("mode", "availability"), ("availability", "mode")):
            d = Dispatcher(8, 2)
            d.set_lift_available(0, 0, False)
            for callback in order:
                if callback == "mode":
                    d.set_mode(10, "fire")
                else:
                    d.set_lift_available(10, 0, True)
            self.assertEqual(d.step(10, [4, 0])[0], "down")

        # Reversing the order at fire end also restores normal service.
        for order in (("mode", "availability"), ("availability", "mode")):
            d = Dispatcher(8, 2)
            d.set_mode(10, "fire")
            d.set_lift_available(11, 0, False)
            for callback in order:
                if callback == "mode":
                    d.set_mode(20, "normal")
                else:
                    d.set_lift_available(20, 0, True)
            self.assertEqual(d.step(20, [4, 0])[0], "stay")

    def test_withdrawal_boundary_callbacks_are_order_independent(self):
        for order in (("mode", "availability"), ("availability", "mode")):
            d = Dispatcher(8, 2)
            for callback in order:
                if callback == "mode":
                    d.set_mode(10, "fire")
                else:
                    d.set_lift_available(10, 0, False)
            self.assertEqual(d.step(10, [4, 0])[0], "stay")
            for callback in order:
                if callback == "mode":
                    d.set_mode(20, "normal")
                else:
                    d.set_lift_available(20, 0, True)
            self.assertEqual(d.step(20, [4, 0])[0], "stay")

    def test_long_fire_and_all_unavailable_keep_safety_commands(self):
        d = Dispatcher(4, 2)
        d.set_mode(60, "fire")
        d.set_lift_available(61, 0, False)
        # Fire may outlast all ordinary work; unavailable always stays while
        # an available lift at ground continues to receive open.
        for t in range(62, 200):
            self.assertEqual(d.step(t, [0, 0]), ["stay", "open"])
        d.set_lift_available(200, 1, False)
        self.assertEqual(d.step(200, [0, 0]), ["stay", "stay"])
        d.set_mode(201, "normal")
        self.assertEqual(d.step(201, [0, 0]), ["stay", "stay"])

    def test_fire_recall_never_moves_up_and_holds_open_after_deadline(self):
        d = Dispatcher(6, 2)
        d.set_mode(20, "fire")
        # During the recall window, both cars can only descend or open at 0.
        for t, positions in ((20, [5, 0]), (21, [4, 0]), (22, [3, 0]),
                             (23, [2, 0]), (24, [1, 0]), (25, [0, 0])):
            commands = d.step(t, positions)
            self.assertNotIn("up", commands)
            self.assertNotIn("open", [c for p, c in zip(positions, commands) if p != 0])
        # floors + 2 = 8 seconds after fire start. At and after that tick,
        # every in-service lift at ground must receive open on each tick.
        self.assertEqual(d.step(28, [0, 0]), ["open", "open"])
        self.assertEqual(d.step(29, [0, 0]), ["open", "open"])

    def test_short_fire_preserves_rider_when_lift_reaches_zero_on_final_fire_tick(self):
        # Fire is active on [60, 70). The lift reaches zero on the last fire
        # tick, but normal mode is delivered before the next step, so no fire
        # opening occurs and the passenger remains aboard.
        d = Dispatcher(30, 1)
        w = World(d, floors=30, positions=[10])
        rider = {"origin": 10, "dest": 3, "start": 59}
        for t in range(60):
            w.tick(t)
        w.register(rider)
        d.on_car_request(59, 0, 3)
        w.riders[0].append(rider)
        self.assertEqual(w.pos, [10])
        w.set_mode(60, "fire")
        for t in range(60, 70):
            w.tick(t)
        self.assertEqual(w.pos, [0])
        self.assertEqual(w.riders[0], [rider])
        self.assertEqual(w.evacuated, [])
        w.set_mode(70, "normal")
        for t in range(70, 150):
            w.tick(t)
        self.assertEqual(w.evacuated, [])
        self.assertEqual(len(w.done), 1)
        self.assertIs(w.done[0][0], rider)
        self.assertEqual(w.done[0][0]["start"], 59)

    def test_ten_second_fire_can_end_before_recall_and_rider_survives(self):
        # The rider is aboard when a design-valid [60, 70) fire begins. Fire
        # ends before the recall deadline, so the rider stays aboard.
        d = Dispatcher(30, 1)
        w = World(d, positions=[29])
        rider = {"origin": 29, "dest": 28, "start": 0}
        for t in range(60):
            w.tick(t)
        rider["start"] = 59
        w.register(rider)
        d.on_car_request(59, 0, 28)
        w.riders[0].append(rider)
        w.set_mode(60, "fire")
        w.set_mode(70, "normal")
        for t in range(60, 70):
            w.tick(t)
        self.assertEqual(w.pos, [19])
        self.assertEqual(w.riders[0], [rider])
        for t in range(70, 150):
            w.tick(t)
        self.assertEqual(w.evacuated, [])
        self.assertEqual(len(w.done), 1)
        self.assertIs(w.done[0][0], rider)
        self.assertLessEqual(w.done[0][1] - rider["start"], 150)

    def test_withdrawal_during_recall_requeues_rider_at_physical_floor(self):
        d = Dispatcher(10, 2)
        w = World(d, floors=10, positions=[9, 9])
        rider = {"origin": 9, "dest": 8, "start": 59}
        w.register(rider)
        w.riders[0].append(rider)
        # Preserve independent work in the other car while car 0 is recalled.
        other = {"origin": 9, "dest": 2, "start": 59}
        w.register(other)
        w.riders[1].append(other)
        for t in range(59):
            w.tick(t)
        d.on_car_request(59, 0, 8)
        d.on_car_request(59, 1, 2)
        w.tick(59)
        self.assertEqual(w.pos, [8, 8])
        self.assertIn(rider, w.riders[0])
        self.assertIn(other, w.riders[1])
        w.set_mode(60, "fire")
        w.set_lift_available(63, 0, False)
        w.set_mode(80, "normal")
        w.set_lift_available(100, 0, True)
        for t in range(60, 64):
            w.tick(t)
        # Both cars descend 8 -> 5 on fire ticks 60..62. Withdrawal arrives
        # before tick 63's step and requeues the same passenger there, while
        # car 1 descends to 4 with its request intact.
        self.assertTrue(any(p is rider for p in w.waiting.get(5, [])))
        self.assertEqual(rider["origin"], 9)
        self.assertEqual(rider["start"], 59)
        self.assertEqual(w.pos[0], 5)
        self.assertEqual(w.riders[0], [])
        self.assertEqual(w.riders[1], [other])
        self.assertEqual(w.pos[1], 4)
        for t in range(64, 300):
            w.tick(t)
        self.assertTrue(any(p is other for p in w.evacuated))
        self.assertEqual(len(w.done), 1)
        self.assertIs(w.done[0][0], rider)
        self.assertEqual(rider["origin"], 9)
        self.assertLessEqual(w.done[0][1] - rider["start"], 300)

    def test_mode_transitions_are_exact_and_instance_local(self):
        a, b = Dispatcher(6, 1), Dispatcher(6, 1)
        a.on_car_request(0, 0, 4)
        a.set_mode(1, "fire")
        a.set_mode(2, "fire")  # repeated fire must not erase the obligation
        a.set_mode(3, "invalid")
        self.assertEqual(a.step(3, [4]), ["down"])
        self.assertEqual(b.step(3, [4]), ["stay"])
        a.set_mode(4, "normal")
        self.assertEqual(a.step(4, [4]), ["open"])

    def test_recall_and_return_during_fire_use_applied_positions(self):
        # Start at the top, withdraw the second lift, then return it high up.
        # The oracle checks physical positions before every command and applies
        # each command, so a timely-looking command cannot hide a missed recall.
        w = World(Dispatcher(8, 2), floors=8, positions=[7, 6])
        w.set_mode(10, "fire")
        w.set_lift_available(11, 1, False)
        w.set_lift_available(14, 1, True)
        w.set_mode(30, "normal")
        w.run(30, 100)
        self.assertEqual(w.pos, [0, 0])

    def test_high_floor_return_after_global_deadline_gets_own_recall_window(self):
        # Global deadline is 92. Lift 2 returns at 100 from floor 29, so its
        # individual deadline is 132; the World oracle checks every tick.
        w = World(Dispatcher(30, 3), positions=[0, 0, 29])
        w.set_lift_available(0, 2, False)
        w.set_mode(60, "fire")
        w.set_lift_available(100, 2, True)
        w.set_mode(180, "normal")
        for t in range(60):
            w.tick(t)
        for t in range(60, 100):
            w.tick(t)
        self.assertEqual(w.pos[2], 29)
        self.assertEqual(w.available(2), False)
        self.assertEqual(w.pos[0], 0)
        self.assertEqual(w.pos[1], 0)
        w.tick(100)
        self.assertEqual(w.pos[2], 28)
        self.assertTrue(w.available(2))
        for t in range(101, 133):
            w.tick(t)
        self.assertEqual(w.pos[2], 0)
        self.assertIn((132, 2, 0, "open"), w.fire_commands)
        for t in range(133, 180):
            w.tick(t)
            self.assertEqual(w.pos[2], 0)
        self.assertTrue(all((t, 2, 0, "open") in w.fire_commands for t in range(132, 180)))

    def test_fire_opening_at_ground_does_not_board_floor_zero_waiters(self):
        d = Dispatcher(5, 2)
        w = World(d, floors=5, positions=[0, 4])
        w.arrival(0, 0, 3)
        w.set_mode(0, "fire")
        w.set_mode(10, "normal")
        w.run(10, 100)
        self.assertEqual(w.evacuated, [])
        self.assertEqual(len(w.done), 1)
        self.assertEqual(w.done[0][0]["origin"], 0)

    def test_fire_contract_returns_open_at_zero_and_stay_when_unavailable(self):
        d = Dispatcher(8, 3)
        d.set_mode(10, "fire")
        d.set_lift_available(10, 1, False)
        self.assertEqual(d.step(10, [0, 3, 7]), ["open", "stay", "down"])
        for args in [(11, "other"), (12, None)]:
            d.set_mode(*args)
        self.assertEqual(d.step(11, [0, 3, 7]), ["open", "stay", "down"])
        d.set_lift_available(12, 1, True)
        self.assertEqual(d.step(12, [0, 3, 7]), ["open", "down", "down"])
        d.set_mode(13, "normal")
        self.assertEqual(d.step(13, [0, 3, 7])[0], "stay")

    def test_fire_evacuation_ignores_car_destinations_and_requeues_waiters(self):
        d = Dispatcher(8, 3)
        w = World(d, floors=8, positions=[4, 0, 7])
        d.on_car_request(0, 0, 7)
        w.riders[0] = [{"origin": 1, "dest": 7, "start": 0}]
        w.arrival(0, 3, 6)
        w.set_mode(0, "fire")
        w.set_mode(20, "normal")
        w.run(80, 300)
        self.assertEqual(len(w.evacuated), 1)
        self.assertEqual(len(w.done), 1)
        self.assertEqual(w.done[0][0]["origin"], 3)
        self.assertLessEqual(w.done[0][1], 300)

    def test_fire_respects_delayed_return_and_normal_v4_traffic_sample(self):
        w = World(Dispatcher(30, 3))
        arrivals = make_v2_day(777)
        for t, origin, dest in arrivals:
            w.arrival(t, origin, dest)
        w.set_lift_available(0, 0, False)
        w.set_lift_available(100, 1, False)
        w.set_lift_available(220, 1, True)
        w.set_mode(120, "fire")
        w.set_mode(180, "normal")
        w.run(599, 3000)
        self.assertEqual(len(w.done) + len(w.evacuated), 120)
        self.assertLessEqual(max(t - p["start"] for p, t in w.done), 590)

    def test_returning_lift_gets_fire_recovery_window(self):
        d = Dispatcher(8, 2)
        d.set_mode(5, "fire")
        d.set_lift_available(5, 0, False)
        d.set_lift_available(8, 0, True)
        # It is physically at floor 4 when it returns; downward travel is legal.
        self.assertIn(d.step(8, [4, 0])[0], ("down", "open"))
        for t in range(9, 18):
            commands = d.step(t, [max(0, 4 - (t - 8)), 0])
            self.assertIn(commands[0], ("down", "open"))
        self.assertEqual(d.step(18, [0, 0]), ["open", "open"])

    def test_short_fire_keeps_unopened_car_destination_without_callback_replay(self):
        d = Dispatcher(8, 2)
        w = World(d, floors=8, positions=[4, 0])
        d.on_car_request(0, 0, 7)
        w.riders[0] = [{"origin": 1, "dest": 7, "start": 0}]
        w.set_mode(0, "fire")
        w.set_mode(1, "normal")
        w.run(1, 40)
        self.assertEqual(len(w.done), 1)
        self.assertEqual(w.done[0][0]["dest"], 7)
        self.assertEqual(w.evacuated, [])

    def test_recall_deadline_is_applied_to_physical_positions(self):
        w = World(Dispatcher(8, 2), floors=8, positions=[7, 0])
        w.set_mode(3, "fire")
        w.set_lift_available(5, 1, False)
        w.set_lift_available(6, 1, True)
        w.run(17, 40)
        # The simulator oracle checks each active lift at its own deadline,
        # including the second car's return deadline at tick 16.

    def test_unavailable_stays_in_fire_and_normal_and_one_floor_is_safe(self):
        d = Dispatcher(1, 2)
        d.set_lift_available(0, 0, False)
        d.set_mode(0, "fire")
        self.assertEqual(d.step(0, [0, 0]), ["stay", "open"])
        self.assertEqual(d.step(1, [0, 0]), ["stay", "open"])
        d.set_mode(2, "normal")
        self.assertEqual(d.step(2, [0, 0]), ["stay", "stay"])


if __name__ == "__main__":
    unittest.main()
