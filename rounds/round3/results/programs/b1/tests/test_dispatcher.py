"""Black-box tests for the lift building contract and v1 traffic promise."""

import random
import unittest

from dispatcher import Dispatcher


COMMANDS = {"up", "down", "stay", "open"}


class Passenger:
    def __init__(self, started, origin, destination):
        self.started = started
        self.origin = origin
        self.destination = destination
        self.completed = None


class Building:
    """One-car tick simulator: events, step, then apply command."""

    def __init__(self, dispatcher, arrivals=(), initial=()):
        self.dispatcher = dispatcher
        self.arrivals = {}
        self.passengers = []
        self.waiting = {}
        self.onboard = []
        self.floor = 0
        self.commands = []
        self.next_tick = 0
        assert dispatcher.lifts == 1
        assert all(type(t) is int and t >= 0 and type(o) is int and type(d) is int
                   and 0 <= o < dispatcher.floors and 0 <= d < dispatcher.floors
                   and o != d and type(n) is int and n > 0
                   for t, o, d, n in arrivals)
        assert len(initial) <= 10
        for tick, origin, destination, count in arrivals:
            self.arrivals.setdefault(tick, []).extend(
                (origin, destination) for _ in range(count))
        for origin, destination in initial:
            assert type(origin) is int and type(destination) is int
            assert origin == self.floor and 0 <= destination < dispatcher.floors
            assert destination != origin
            p = Passenger(0, origin, destination)
            self.passengers.append(p)
            self.onboard.append(p)
            dispatcher.on_car_request(0, 0, destination)

    def tick(self, t):
        if t != self.next_tick:
            raise AssertionError("ticks must continue monotonically: expected %d, got %d" %
                                 (self.next_tick, t))
        self.next_tick += 1
        # Every original passenger appears before step on their arrival tick.
        for origin, destination in self.arrivals.get(t, ()):
            p = Passenger(t, origin, destination)
            self.passengers.append(p)
            self.waiting.setdefault(origin, []).append(p)
            self.dispatcher.on_call(t, origin,
                                     "up" if destination > origin else "down")
        commands = self.dispatcher.step(t, [self.floor])
        self.commands.append(commands)
        if len(commands) != 1 or commands[0] not in COMMANDS:
            raise AssertionError("invalid command vector: %r" % (commands,))
        command = commands[0]
        if command == "up":
            if self.floor >= self.dispatcher.floors - 1:
                raise AssertionError("commanded above top floor")
            self.floor += 1
        elif command == "down":
            if self.floor <= 0:
                raise AssertionError("commanded below floor 0")
            self.floor -= 1
        elif command == "open":
            # Unload before boarding, then produce car buttons and overflow recall.
            for p in self.onboard:
                if p.destination == self.floor:
                    p.completed = t
            self.onboard = [p for p in self.onboard
                            if p.destination != self.floor]
            queue = self.waiting.get(self.floor, [])
            room = 10 - len(self.onboard)
            boarded, remaining = queue[:room], queue[room:]
            self.onboard.extend(boarded)
            self.waiting[self.floor] = remaining
            for p in boarded:
                self.dispatcher.on_car_request(t, 0, p.destination)
            if remaining:
                # The building repeats the hall call after this open is applied.
                direction = "up" if remaining[0].destination > self.floor else "down"
                self.dispatcher.on_call(t, self.floor, direction)
        active = [p for queue in self.waiting.values() for p in queue] + self.onboard
        assert len({id(p) for p in active}) == len(active)
        assert len(active) + sum(p.completed is not None for p in self.passengers) == len(self.passengers)

    def run(self, last_arrival, max_ticks=2000):
        final_arrival = max([last_arrival] + list(self.arrivals))
        for t in range(self.next_tick, max_ticks):
            self.tick(t)
            if t >= final_arrival and all(p.completed is not None
                                         for p in self.passengers):
                return
        raise AssertionError("passengers did not all finish by %d" % max_ticks)


class BuildingGroup:
    """Multi-car simulator implementing shared hall calls and car buttons."""
    def __init__(self, dispatcher, arrivals=(), outages=(), initial=(), floors=None):
        self.dispatcher = dispatcher
        self.arrivals = {}
        self.passengers = []
        self.waiting = {}
        self.onboard = [[] for _ in range(dispatcher.lifts)]
        self.floors = list(floors) if floors is not None else [0] * dispatcher.lifts
        assert len(self.floors) == dispatcher.lifts
        assert all(type(f) is int and 0 <= f < dispatcher.floors for f in self.floors)
        assert all(type(t) is int and t >= 0 and type(o) is int and type(d) is int
                   and 0 <= o < dispatcher.floors and 0 <= d < dispatcher.floors
                   and o != d and type(n) is int and n > 0
                   for t, o, d, n in arrivals)
        assert all(type(l) is int and 0 <= l < dispatcher.lifts and
                   type(o) is int and o == self.floors[l] and type(d) is int and
                   0 <= d < dispatcher.floors and d != o
                   for l, o, d in initial)
        assert all(sum(1 for l, _, _ in initial if l == lift) <= 10
                   for lift in range(dispatcher.lifts))
        self.outages = {}
        self.available = [True] * dispatcher.lifts
        self.evicted_count = 0
        self.requeued_count = 0
        self.evicted_at_destination = 0
        self.outages_with_riders = 0
        self.next_tick = 0
        self.last_outage_tick = max((tick for tick, _, _ in outages), default=-1)
        for tick, lift, available in outages:
            self.outages.setdefault(tick, []).append((lift, available))
        for tick, origin, destination, count in arrivals:
            self.arrivals.setdefault(tick, []).extend(
                (origin, destination) for _ in range(count))
        for lift, origin, destination in initial:
            p = Passenger(0, origin, destination)
            self.passengers.append(p)
            self.onboard[lift].append(p)
            dispatcher.on_car_request(0, lift, destination)

    def _assert_conserved(self):
        active = [p for queue in self.waiting.values() for p in queue]
        active.extend(p for car in self.onboard for p in car)
        completed = [p for p in self.passengers if p.completed is not None]
        assert len({id(p) for p in active + completed}) == len(active) + len(completed)
        assert len(active) + len(completed) == len(self.passengers)

    def tick(self, t):
        if t != self.next_tick:
            raise AssertionError("ticks must continue monotonically: expected %d, got %d" %
                                 (self.next_tick, t))
        self.next_tick += 1
        # Maintenance events precede calls and step, just like building events.
        for lift, available in self.outages.get(t, ()):
            self.dispatcher.set_lift_available(t, lift, available)
            if self.available[lift] and not available:
                # Eviction preserves the original clock. Riders at their
                # destination have arrived; everyone else calls again here.
                evicted = self.onboard[lift]
                self.onboard[lift] = []
                self.evicted_count += len(evicted)
                self.outages_with_riders += bool(evicted)
                for p in evicted:
                    if p.destination == self.floors[lift]:
                        p.completed = t
                        self.evicted_at_destination += 1
                    else:
                        # Keep the original journey intact; current location is
                        # represented by the waiting queue key.
                        floor = self.floors[lift]
                        self.waiting.setdefault(floor, []).append(p)
                        self.requeued_count += 1
                        self.dispatcher.on_call(t, floor,
                            "up" if p.destination > floor else "down")
            self.available[lift] = available
        for origin, destination in self.arrivals.get(t, ()):
            p = Passenger(t, origin, destination)
            self.passengers.append(p)
            self.waiting.setdefault(origin, []).append(p)
            self.dispatcher.on_call(t, origin, "up" if destination > origin else "down")
        commands = self.dispatcher.step(t, list(self.floors))
        if len(commands) != len(self.floors) or not set(commands) <= COMMANDS:
            raise AssertionError("invalid command vector: %r" % (commands,))
        for lift, (available, command) in enumerate(zip(self.available, commands)):
            if not available:
                self.assert_command_stay(lift, command, t)
        opening = []
        for lift, (floor, command) in enumerate(zip(self.floors, commands)):
            if command == "up":
                if floor >= self.dispatcher.floors - 1:
                    raise AssertionError("commanded above top floor")
                self.floors[lift] += 1
            elif command == "down":
                if floor <= 0:
                    raise AssertionError("commanded below floor 0")
                self.floors[lift] -= 1
            elif command == "open":
                opening.append((lift, floor))
        # All cars open on the same tick before boarding is allocated. The
        # building can board a waiting passenger only once, in lift order.
        opened_floors = set()
        for lift, floor in opening:
            for p in self.onboard[lift]:
                if p.destination == floor:
                    p.completed = t
            self.onboard[lift] = [p for p in self.onboard[lift] if p.destination != floor]
            queue = self.waiting.get(floor, [])
            room = 10 - len(self.onboard[lift])
            boarded, remaining = queue[:room], queue[room:]
            self.waiting[floor] = remaining
            self.onboard[lift].extend(boarded)
            for p in boarded:
                self.dispatcher.on_car_request(t, lift, p.destination)
            if remaining:
                self.dispatcher.on_call(t, floor,
                    "up" if remaining[0].destination > floor else "down")
            opened_floors.add(floor)
        self._assert_conserved()
        # A simultaneous open at a shared floor sees the same queue; the
        # previous loop's emptied queue guarantees no duplicate boarding.

    def run(self, last_arrival, max_ticks=2000):
        final_event = max([last_arrival, self.last_outage_tick] + list(self.arrivals))
        for t in range(self.next_tick, max_ticks):
            self.tick(t)
            if (t >= final_event and
                    all(p.completed is not None for p in self.passengers)):
                return
        raise AssertionError("passengers did not all finish by %d" % max_ticks)

    @staticmethod
    def assert_command_stay(lift, command, tick):
        if command != "stay":
            raise AssertionError("unavailable lift %d commanded %s at t=%d" %
                                 (lift, command, tick))


def validate_outages(outages, lifts=3):
    """Validate the complete outage schedule; False includes its tick."""
    events = {}
    disabled = set()
    taken_out = set()
    for tick, lift, available in outages:
        assert type(tick) is int and tick >= 0
        assert type(lift) is int and 0 <= lift < lifts
        assert type(available) is bool
        events.setdefault(tick, []).append((lift, available))
    overlap = 0
    overlap_start = None
    last_tick = max(events, default=-1)
    for tick in sorted(events):
        for lift, available in events[tick]:
            if available:
                if lift in disabled:
                    disabled.remove(lift)
                    if len(disabled) == 1 and overlap_start is not None:
                        overlap += tick - overlap_start
                        overlap_start = None
                # Redundant True is an idempotent no-op.
            elif lift not in disabled:
                assert lift not in taken_out, "lift taken out more than once"
                disabled.add(lift)
                taken_out.add(lift)
                assert len(taken_out) <= 2
                assert len(disabled) < lifts
                if len(disabled) == 2:
                    overlap_start = tick
            # Redundant False is an idempotent no-op.
    if len(disabled) == 2:
        raise AssertionError("permanent two-lift overlap exceeds 120 ticks")
    assert overlap <= 120 and (overlap_start is None or last_tick - overlap_start + 1 <= 120), \
        "two-lift overlap exceeds 120 ticks"
    if overlap_start is not None:
        overlap += last_tick - overlap_start + 1
    return overlap


def make_arrivals(seed, clustered=False, total=40):
    """Draw 40 passenger journeys and enforce each rolling arrival cap."""
    rng = random.Random(seed)
    arrivals = []
    counts = [0] * 600
    while sum(item[3] for item in arrivals) < total:
        remaining = total - sum(item[3] for item in arrivals)
        if clustered and not any(n == 12 for _, _, _, n in arrivals):
            count = min(12, remaining)
        else:
            count = 1
        # Keep a requested cluster together; individual arrivals elsewhere may
        # also be at the same tick, so the caps are checked per person below.
        candidates = list(range(600))
        rng.shuffle(candidates)
        chosen = None
        for t in candidates:
            def within(width, cap):
                # Check every rolling window affected by inserting at t,
                # including windows whose endpoint is later than t.
                return all(sum(counts[max(0, end - width + 1):end + 1]) +
                           (count if max(0, end-width+1) <= t <= end else 0) <= cap
                           for end in range(600))
            if within(10, 15) and within(60, 20) and within(300, 35):
                chosen = t
                break
        if chosen is None:
            count = 1
            for t in candidates:
                if (all(sum(counts[max(0, end - 9):end + 1]) +
                        (1 if max(0, end-9) <= t <= end else 0) <= 15
                        for end in range(600)) and
                    all(sum(counts[max(0, end - 59):end + 1]) +
                        (1 if max(0, end-59) <= t <= end else 0) <= 20
                        for end in range(600)) and
                    all(sum(counts[max(0, end - 299):end + 1]) +
                        (1 if max(0, end-299) <= t <= end else 0) <= 35
                        for end in range(600))):
                    chosen = t
                    break
        if chosen is None:
            raise AssertionError("could not draw a valid traffic day")
        origin = rng.randrange(30)
        destination = rng.randrange(29)
        if destination >= origin:
            destination += 1
        arrivals.append((chosen, origin, destination, count))
        counts[chosen] += count
    arrivals.sort()
    validate_day(arrivals, expected_total=total)
    return arrivals


def validate_day(arrivals, initial=(), expected_total=40):
    """Independently check original journey count and every rolling cap."""
    ticks = [0] * 600
    crowd = {}
    total = len(initial)
    ticks[0] += len(initial)
    for origin, destination in initial:
        assert type(origin) is int and type(destination) is int
        assert origin == 0 and 0 <= destination < 30 and destination != origin
    for t, origin, destination, count in arrivals:
        assert 0 <= t < 600 and 0 <= origin < 30 and 0 <= destination < 30
        assert origin != destination and 1 <= count <= 12
        ticks[t] += count
        crowd[(t, origin)] = crowd.get((t, origin), 0) + count
        total += count
    assert total == expected_total
    assert max(crowd.values(), default=0) <= 12
    for width, cap in ((10, 15), (60, 20), (300, 35)):
        for end in range(600):
            assert sum(ticks[max(0, end-width+1):end+1]) <= cap


def make_v2_arrivals(seed, variant=0):
    """120 journeys with a 15-person crowd or a 30-person ten-second burst."""
    rng = random.Random(seed)
    counts = [1] * 120
    if variant == 1:
        counts[:15] = [15] + [0] * 14
    elif variant == 2:
        counts[:30] = [15, 15] + [0] * 28
    arrivals = []
    for i, count in enumerate(counts):
        if not count:
            continue
        # Base schedule is five seconds apart; extra crowd members share a tick.
        t = 100 if variant == 2 and i < 2 else 5 * i
        origin = rng.randrange(30)
        destination = rng.randrange(29)
        if destination >= origin:
            destination += 1
        arrivals.append((t, origin, destination, count))
    arrivals.sort()
    validate_v2_day(arrivals)
    return arrivals


def make_random_v2_arrivals(seed):
    """Draw 120 calls at random ticks while enforcing all v2 rolling caps."""
    rng = random.Random(seed)
    ticks = [0] * 600
    arrivals = []
    for _ in range(120):
        candidates = list(range(600))
        rng.shuffle(candidates)
        for t in candidates:
            valid = True
            for width, cap in ((10, 35), (60, 50), (300, 90)):
                for end in range(t, min(599, t + width - 1) + 1):
                    if sum(ticks[max(0, end-width+1):end+1]) + 1 > cap:
                        valid = False
                        break
                if not valid:
                    break
            if valid:
                break
        else:
            raise AssertionError("could not draw randomized v2 traffic")
        origin = rng.randrange(30)
        destination = rng.randrange(29)
        if destination >= origin:
            destination += 1
        arrivals.append((t, origin, destination, 1))
        ticks[t] += 1
    arrivals.sort()
    validate_v2_day(arrivals)
    return arrivals


def validate_v2_day(arrivals, initial=(), floors=None):
    ticks = [0] * 600
    crowd = {}
    floors = list(floors) if floors is not None else [0] * 3
    assert len(floors) == 3 and all(type(f) is int and 0 <= f < 30 for f in floors)
    total = len(initial)
    ticks[0] += total
    capacity = [0] * 3
    for lift, origin, destination in initial:
        assert type(lift) is int and 0 <= lift < 3
        assert type(origin) is int and type(destination) is int
        assert 0 <= origin < 30 and 0 <= destination < 30 and origin != destination
        assert origin == floors[lift]
        capacity[lift] += 1
    assert max(capacity, default=0) <= 10
    for t, origin, destination, count in arrivals:
        assert 0 <= t < 600 and 0 <= origin < 30 and 0 <= destination < 30
        assert origin != destination and 1 <= count <= 15
        ticks[t] += count
        crowd[(t, origin)] = crowd.get((t, origin), 0) + count
        total += count
    assert total == 120
    assert max(crowd.values(), default=0) <= 15
    for width, cap in ((10, 35), (60, 50), (300, 90)):
        for end in range(600):
            assert sum(ticks[max(0, end-width+1):end+1]) <= cap


class DispatcherTests(unittest.TestCase):
    def test_interface_safety_and_defensive_inputs(self):
        d = Dispatcher(30, 2)
        for method, args in ((d.on_call, (0, 29, "up")),
                             (d.on_call, (0, -1, "up")),
                             (d.on_call, (0, 3, "sideways")),
                             (d.on_car_request, (0, 99, 2)),
                             (d.on_car_request, (0, 1, 29)),
                             (d.on_car_request, (0, 0, 0))):
            method(*args)
        for t in range(80):
            floors = [min(29, t // 2), 0]
            commands = d.step(t, floors)
            self.assertEqual(len(commands), 2)
            self.assertTrue(set(commands) <= COMMANDS)
            for floor, command in zip(floors, commands):
                self.assertFalse(command == "up" and floor == 29)
                self.assertFalse(command == "down" and floor == 0)

    def test_fixed_contract_cases(self):
        # Long idle-to-top trip verifies bounds and that distant calls are served.
        b = Building(Dispatcher(30, 1), [(0, 29, 0, 1)])
        b.run(0)
        self.assertEqual(b.passengers[0].completed, 59)

        # Initial car request starts the clock at zero and needs an opening tick.
        b = Building(Dispatcher(30, 1), initial=[(0, 2)])
        b.run(0)
        self.assertEqual(b.passengers[0].completed, 2)

        # Both hall directions at one floor merge to one stop; opening boards both.
        b = Building(Dispatcher(10, 1), [(0, 4, 8, 1), (0, 4, 1, 1)])
        b.run(0)
        self.assertEqual(len(b.passengers), 2)
        self.assertTrue(all(p.completed is not None for p in b.passengers))

        # A request arriving on an open tick and one on the following tick survive.
        b = Building(Dispatcher(10, 1), [(0, 0, 3, 1), (1, 0, 2, 1)])
        b.run(1)
        self.assertTrue(all(p.completed is not None for p in b.passengers))

        # A twelve-person crowd forces an overflow recall and a second trip.
        b = Building(Dispatcher(30, 1), [(0, 5, 25, 12)])
        b.run(0)
        self.assertEqual(len(b.passengers), 12)
        self.assertTrue(all(p.completed is not None for p in b.passengers))
        self.assertGreaterEqual(sorted(p.completed for p in b.passengers)[-1], 51)

        # A fresh hall call after unloading at the same floor must not be
        # suppressed by the prior opening.
        b = Building(Dispatcher(10, 1), [(3, 2, 3, 1)], initial=[(0, 2)])
        b.run(3)
        self.assertLessEqual(b.passengers[1].completed - b.passengers[1].started, 3)

        # Idle opening followed by a same-floor arrival, plus repeated arrivals.
        b = Building(Dispatcher(10, 1), [(0, 0, 1, 1), (2, 0, 2, 1),
                                         (3, 0, 3, 1)])
        b.run(3)
        self.assertTrue(all(p.completed is not None for p in b.passengers))

    def test_seeded_traffic_envelope_worst_passenger(self):
        # Include concentrated 12-person days and initially occupied cars.
        seeds = list(range(500))
        worst = (0, None, None)
        for seed in seeds:
            arrivals = make_arrivals(seed, clustered=(seed % 4 == 0))
            b = Building(Dispatcher(30, 1), arrivals)
            b.run(599)
            for p in b.passengers:
                elapsed = p.completed - p.started
                if elapsed > worst[0]:
                    worst = (elapsed, seed, p)
                self.assertLessEqual(elapsed, 270,
                                     "seed %d passenger %d->%d took %ds" %
                                     (seed, p.origin, p.destination, elapsed))
        self.assertLessEqual(worst[0], 270)
        self.assertEqual(len(seeds), 500)
        print("v1 hall: 500 seeds 0-499; worst %ds seed %s journey %d->%d started %d completed %d" %
              (worst[0], worst[1], worst[2].origin, worst[2].destination,
               worst[2].started, worst[2].completed))

    def test_seeded_envelope_with_initial_riders(self):
        # Initial riders are part of the day's 40 journeys, not extra arrivals.
        # Their clocks start at t=0 and they occupy the car before tick 0.
        seeds = list(range(500, 1000))
        worst = (0, None, None)
        for seed in seeds:
            rng = random.Random(seed)
            initial = []
            for _ in range(2):
                origin = rng.randrange(30)
                destination = rng.randrange(29)
                if destination >= origin:
                    destination += 1
                initial.append((origin, destination))
            # Initial occupants must start at the actual car position, floor 0.
            initial = [(0, rng.randrange(1, 30)) for _ in range(2)]
            arrivals = make_arrivals(seed, clustered=(seed % 4 == 0), total=38)
            validate_day(arrivals, initial)
            b = Building(Dispatcher(30, 1), arrivals, initial=initial)
            b.run(599)
            self.assertEqual(len(b.passengers), 40)
            for p in b.passengers:
                elapsed = p.completed - p.started
                if elapsed > worst[0]:
                    worst = (elapsed, seed, p)
                self.assertLessEqual(elapsed, 270,
                                     "seed %d passenger %d->%d took %ds" %
                                     (seed, p.origin, p.destination, elapsed))
        self.assertLessEqual(worst[0], 270)
        self.assertEqual(len(seeds), 500)
        print("v1 initial: 500 seeds 500-999; worst %ds seed %s journey %d->%d started %d completed %d" %
              (worst[0], worst[1], worst[2].origin, worst[2].destination,
               worst[2].started, worst[2].completed))

    def test_final_envelope_validator_catches_late_window_violation(self):
        # Inserting a call at t=1 can invalidate the 60-tick window ending at
        # t=11. A validator that checks only windows ending at each insertion
        # time misses this when arrivals are assembled out of chronological order.
        arrivals = [(11, floor, 29, 1) for floor in range(20)]
        arrivals += [(1, 20, 29, 1)]
        arrivals += [(100 + i, i % 29, 29, 1) for i in range(19)]
        with self.assertRaises(AssertionError):
            validate_day(arrivals, expected_total=40)


class MultiLiftTests(unittest.TestCase):
    def test_simulator_continuation_does_not_replay_events(self):
        for make in (lambda: Building(Dispatcher(10, 1), [(0, 0, 2, 1)]),
                     lambda: BuildingGroup(Dispatcher(10, 3), [(0, 0, 2, 1)])):
            b = make()
            b.tick(0)
            b.run(0)
            self.assertEqual(len(b.passengers), 1)
            self.assertEqual(b.passengers[0].started, 0)

    def test_simulator_rejects_invalid_initial_state(self):
        with self.assertRaises(AssertionError):
            validate_day([], initial=[(0, 30)])
        with self.assertRaises(AssertionError):
            Building(Dispatcher(10, 1), initial=[(0, 10)])
        for kwargs in ({"floors": [0, 1]}, {"floors": [0, 0, 30]},
                       {"initial": [(0, 1, 4)]},
                       {"initial": [(0, 0, 4)] * 11}):
            with self.assertRaises(AssertionError):
                BuildingGroup(Dispatcher(10, 3), **kwargs)

    def test_future_events_are_not_skipped_by_last_arrival_hint(self):
        b = Building(Dispatcher(10, 1), [(8, 0, 2, 1)])
        b.run(0)
        self.assertEqual(len(b.passengers), 1)
        self.assertEqual(b.passengers[0].completed, 11)
        b = BuildingGroup(Dispatcher(10, 3), [(8, 0, 2, 1)],
                          outages=[(12, 2, False), (14, 2, True)])
        b.run(0)
        self.assertEqual(len(b.passengers), 1)
        self.assertEqual(b.available[2], True)

    def test_v2_validator_counts_initial_riders_in_tick_zero_budget(self):
        arrivals = make_v2_arrivals(7)
        # Replace one ordinary arrival by an initial passenger: total stays 120.
        arrivals = arrivals[1:]
        initial = [(0, 0, 1)]
        validate_v2_day(arrivals, initial=initial, floors=[0, 0, 0])
        # Tick-zero load is included in rolling limits even when hall arrivals
        # alone would pass them.
        arrivals_at_zero = [(0, i, (i + 1) % 30, 15) for i in range(3)]
        arrivals_at_zero = [(t, o, d, n) for t, o, d, n in arrivals_at_zero
                            if o != d]
        with self.assertRaises(AssertionError):
            validate_v2_day(arrivals_at_zero + [(t, o, d, n)
                for t, o, d, n in make_v2_arrivals(8)[3:]], initial=initial,
                floors=[0, 0, 0])
        with self.assertRaises(AssertionError):
            validate_v2_day(arrivals, initial=initial, floors=[1, 0, 0])
        with self.assertRaises(AssertionError):
            validate_v2_day(arrivals, initial=initial * 2, floors=[0, 0, 0])

    def test_availability_callbacks_are_idempotent_and_isolated(self):
        from modes import LiftAvailability

        state = LiftAvailability(2)
        old_snapshot = state.snapshot()
        self.assertEqual(old_snapshot, (True, True))
        self.assertTrue(state.set_available(0, False))
        self.assertFalse(state.set_available(0, False))
        self.assertTrue(state.set_available(0, True))
        self.assertFalse(state.set_available(0, True))
        self.assertEqual(old_snapshot, (True, True))
        self.assertEqual(state.snapshot(), (True, True))
        for lift, available in ((-1, False), (2, False), (True, False),
                                (0, 1), (0, None)):
            self.assertFalse(state.set_available(lift, available))
            self.assertEqual(state.snapshot(), (True, True))

        # Exercise invalid callback inputs through the public dispatcher while
        # loaded work exists; they must not alter the command trace.
        baseline = Dispatcher(12, 2)
        defensive = Dispatcher(12, 2)
        for d in (baseline, defensive):
            d.on_car_request(0, 0, 8)
            d.on_car_request(0, 1, 6)
        for lift, available in ((-1, False), (2, False), (True, False),
                                (0, 1), (0, None)):
            defensive.set_lift_available(1, lift, available)
        for t, floors in ((1, [0, 0]), (2, [1, 1]), (3, [2, 2])):
            self.assertEqual(baseline.step(t, floors), defensive.step(t, floors))

        # A redundant return callback must preserve loaded work exactly.
        baseline = Dispatcher(12, 1)
        redundant = Dispatcher(12, 1)
        for d in (baseline, redundant):
            d.on_car_request(0, 0, 8)
            d.set_lift_available(1, 0, False)
            d.set_lift_available(2, 0, True)
        redundant.set_lift_available(3, 0, True)
        self.assertEqual(baseline.step(4, [0]), redundant.step(4, [0]))
        self.assertEqual(baseline.step(5, [1]), redundant.step(5, [1]))

    def test_outage_drops_only_its_car_work_and_return_starts_empty(self):
        d = Dispatcher(30, 3)
        d.on_car_request(0, 0, 20)
        d.on_car_request(0, 1, 8)
        d.set_lift_available(1, 0, False)
        self.assertEqual(d.step(1, [7, 0, 29])[0], "stay")
        # A car button while unavailable is ignored.
        d.on_car_request(1, 0, 3)
        d.set_lift_available(2, 0, True)
        # The stale destination 20 and ignored destination 3 must not resume.
        self.assertEqual(d.step(2, [12, 1, 29])[0], "stay")
        # Car 1's destination remains active throughout car 0's outage.
        self.assertEqual(d.step(3, [12, 2, 29])[1], "up")
        # A fresh request after return is accepted and served.
        d.on_car_request(4, 0, 14)
        self.assertEqual(d.step(4, [12, 2, 29])[0], "up")

    def test_outage_releases_and_reassigns_owned_hall_floor(self):
        d = Dispatcher(30, 3)
        d.on_call(0, 4, "up")
        d.step(0, [0, 15, 29])
        former_owner = d._owners[4]
        d.set_lift_available(1, former_owner, False)
        self.assertNotIn(former_owner, d._owners.values())
        d.step(1, [0, 15, 29])
        self.assertIn(4, d._owners)
        self.assertNotEqual(d._owners[4], former_owner)
        d.step(2, [1, 15, 28])
        self.assertIn(4, d._hall)

    def test_outage_validator_boundaries(self):
        self.assertEqual(validate_outages([(0, 0, False)]), 0)
        self.assertEqual(validate_outages([(0, 0, False),
                                          (0, 1, False),
                                          (120, 1, True)]), 120)
        with self.assertRaises(AssertionError):
            validate_outages([(0, 0, False), (0, 1, False), (121, 1, True)])
        with self.assertRaises(AssertionError):
            validate_outages([(0, 0, False), (1, 0, True),
                              (2, 0, False)])
        with self.assertRaises(AssertionError):
            validate_outages([(0, 0, False), (0, 1, False)])
        # Permanent two-car outage remains invalid even if the calls finish early.
        with self.assertRaises(AssertionError):
            validate_outages([(0, 0, False), (0, 1, False)])
        self.assertEqual(validate_outages([(2000, 0, False),
                                           (2000, 1, False),
                                           (2120, 1, True)]), 120)
        with self.assertRaises(AssertionError):
            validate_outages([(2000, 0, False),
                              (2000, 1, False),
                              (2121, 1, True)])
        with self.assertRaises(AssertionError):
            validate_outages([(0, 0, False), (1, 1, False),
                              (2, 0, True), (3, 2, False)])
        self.assertEqual(validate_outages([(0, 0, False), (5, 0, False),
                                           (10, 0, True), (11, 0, True)]), 0)

    def test_maintenance_fixed_cases(self):
        # A rider evicted at the destination is already complete.
        d = Dispatcher(10, 3)
        b = BuildingGroup(d, outages=[(0, 0, False)])
        p = Passenger(0, 0, 0)
        b.passengers.append(p)
        b.onboard[0].append(p)
        d.on_car_request(0, 0, 0)
        b.floors[0] = 0
        b.tick(0)
        self.assertEqual(p.completed, 0)
        self.assertEqual(d.step(1, b.floors)[0], "stay")

        # A full car stopped mid-trip is reboarded and drained to its destination;
        # the original clock remains nonzero throughout the requeue.
        d = Dispatcher(30, 3)
        b = BuildingGroup(d, outages=[(5, 0, False)])
        riders = [Passenger(0, 0, 20) for _ in range(10)]
        b.passengers.extend(riders)
        b.onboard[0].extend(riders)
        for _ in riders:
            d.on_car_request(0, 0, 20)
        b.floors[0] = 7
        b.run(5)
        self.assertTrue(all(p.started == 0 and p.origin == 0 for p in riders))
        self.assertTrue(all(p.completed is not None and p.completed > 5 for p in riders))
        self.assertGreater(b.floors[0], 7)

        # An outage during open takes precedence and leaves the hall work to
        # the other cars. A returned car receives no replayed calls.
        d = Dispatcher(10, 3)
        d.on_call(0, 4, "up")
        d.set_lift_available(0, 0, False)
        commands = d.step(0, [4, 4, 9])
        self.assertEqual(commands[0], "stay")
        # The disabled car is parked at the call floor. The active car at the
        # same floor must still receive the hall stop on this tick.
        self.assertEqual(commands[1], "open")
        d.set_lift_available(0, 0, True)
        cmds = d.step(1, [4, 4, 9])
        self.assertEqual(len(cmds), 3)
        self.assertTrue(set(cmds) <= COMMANDS)

        # A hall request survives an outage and can be served after return,
        # even when the two other cars are full.
        d = Dispatcher(30, 3)
        d.on_call(0, 20, "up")
        for lift in (0, 1):
            for _ in range(10):
                d.on_car_request(0, lift, 25)
        d.set_lift_available(0, 2, False)
        d.step(0, [0, 0, 0])
        d.set_lift_available(1, 2, True)
        cmds = d.step(1, [0, 0, 0])
        self.assertEqual(cmds[2], "up")

        # A returning lift is usable while the other two cars are full.
        d = Dispatcher(30, 3)
        for lift in (0, 1):
            for _ in range(10):
                d.on_car_request(0, lift, 20)
        d.set_lift_available(0, 2, False)
        d.set_lift_available(1, 2, True)
        cmds = d.step(1, [0, 0, 29])
        self.assertEqual(cmds[0], "up")
        self.assertEqual(cmds[1], "up")
        self.assertIn(cmds[2], COMMANDS)

    def test_out_car_at_hall_floor_does_not_consume_call(self):
        # The unavailable car is parked on the call floor. An available car
        # there must still open, board the passenger, and complete the trip.
        b = BuildingGroup(Dispatcher(10, 3), arrivals=[(0, 4, 6, 1)],
                          outages=[(0, 0, False)], floors=[4, 4, 9])
        b.run(0)
        self.assertEqual(b.passengers[0].completed, 3)
        self.assertEqual(b.onboard[0], [])
        self.assertEqual(b.onboard[1], [])

    def test_redundant_return_preserves_live_car_work(self):
        # Compare complete command traces through destination service while
        # the car has duplicate-destination riders and a live hall request.
        ordinary = Dispatcher(12, 1)
        repeated = Dispatcher(12, 1)
        for d in (ordinary, repeated):
            d.on_car_request(0, 0, 8)
            d.on_car_request(0, 0, 8)
            d.on_call(0, 5, "up")
        repeated.set_lift_available(1, 0, True)
        floors = [0]
        for t in range(3, 30):
            a = ordinary.step(t, floors)
            b = repeated.step(t, floors)
            self.assertEqual(a, b)
            if a[0] == "up":
                floors[0] += 1
            elif a[0] == "down":
                floors[0] -= 1
            elif a[0] == "open" and floors[0] == 8:
                break
        else:
            self.fail("live car destinations were not opened")

    def test_returning_car_completes_hall_trip_while_peers_are_full(self):
        initial = [(lift, 0, 25) for lift in (0, 1) for _ in range(10)]
        b = BuildingGroup(Dispatcher(30, 3), arrivals=[(0, 20, 29, 1)],
                          outages=[(0, 2, False), (1, 2, True)],
                          initial=initial, floors=[0, 0, 29])
        b.run(0)
        passenger = next(p for p in b.passengers if p.origin == 20)
        self.assertIsNotNone(passenger.completed)
        self.assertGreater(passenger.completed, 1)
        self.assertEqual(len(b.passengers), 21)
        self.assertTrue(all(p.completed is not None for p in b.passengers))

    def test_seeded_maintenance_days_keep_original_deadline_clocks(self):
        worst = (0, None)
        worst_passenger = None
        for seed in range(12):
            arrivals = make_v2_arrivals(seed, seed % 3)
            # One car is unavailable from t=0; a second has a bounded outage.
            start = 100 + seed * 3
            outages = [(0, 0, False), (start, 1, False),
                       (start + (120 if seed % 3 == 0 else 45), 1, True)]
            self.assertEqual(validate_outages(outages),
                             120 if seed % 3 == 0 else 45)
            b = BuildingGroup(Dispatcher(30, 3), arrivals, outages)
            b.floors = [0, 15, 29]
            # Varied starting positions ensure cars are not all dispatched
            # from the lobby; the fixed case below covers full-car eviction.
            b.run(599)
            for p in b.passengers:
                self.assertIsNotNone(p.completed)
                elapsed = p.completed - p.started
                if elapsed > worst[0]:
                    worst = (elapsed, seed)
                    worst_passenger = p
                self.assertLessEqual(elapsed, 510,
                    "seed %d passenger %d->%d took %ds" %
                    (seed, p.origin, p.destination, elapsed))
            self.assertEqual(len(b.passengers), 120)
        self.assertLessEqual(worst[0], 510)
        p = worst_passenger
        print("v3 maintenance sampled worst: %ds seed %s journey %d->%d started %d completed %d" %
              (worst[0], worst[1], p.origin, p.destination, p.started, p.completed))

    def test_v2_initial_loads_and_randomized_overlap_maintenance(self):
        initial_worst = (0, None, None)
        outage_worst = (0, None, None)
        measured = {"evicted": 0, "requeued": 0, "destination": 0,
                    "outages_with_riders": 0}
        for seed in (41, 42):
            rng = random.Random(seed)
            floors = [0, 15, 29]
            initial = [(lift, floors[lift], destination)
                       for lift, destination in ((0, 9 + seed % 4),
                                                 (1, 20 + seed % 3),
                                                 (2, 10 + seed % 5))]
            arrivals = make_v2_arrivals(seed, variant=seed % 3)
            # Replace three ordinary calls so initial occupants remain within 120.
            remaining_to_replace = 3
            reduced = []
            for index, (t, origin, destination, count) in enumerate(arrivals):
                removed = min(count, remaining_to_replace)
                remaining_to_replace -= removed
                if count > removed:
                    reduced.append((t, origin, destination, count - removed))
                if not remaining_to_replace:
                    reduced.extend(arrivals[index + 1:])
                    break
            assert remaining_to_replace == 0
            arrivals = reduced
            validate_v2_day(arrivals, initial=initial, floors=floors)
            b = BuildingGroup(Dispatcher(30, 3), arrivals, initial=initial, floors=floors)
            b.run(599)
            for p in b.passengers:
                elapsed = p.completed - p.started
                if elapsed > initial_worst[0]:
                    initial_worst = (elapsed, seed, p)
                self.assertLessEqual(elapsed, 290)
            self.assertEqual(len(b.passengers), 120)

            # Randomized overlapping outage starts and durations, while retaining
            # a third available car and the 120-tick aggregate overlap cap.
            start = 70 + rng.randrange(80)
            first_len = 35 + rng.randrange(35)
            second_start = start + 10 + rng.randrange(25)
            second_len = 30 + rng.randrange(35)
            outages = [(start, seed % 3, False),
                       (second_start, (seed + 1) % 3, False),
                       (start + first_len, seed % 3, True),
                       (second_start + second_len, (seed + 1) % 3, True)]
            validate_outages(outages)
            validate_v2_day(arrivals, initial=initial, floors=floors)
            b = BuildingGroup(Dispatcher(30, 3), arrivals, outages,
                              initial=initial, floors=floors)
            b.run(599)
            measured["evicted"] += b.evicted_count
            measured["requeued"] += b.requeued_count
            measured["destination"] += b.evicted_at_destination
            measured["outages_with_riders"] += b.outages_with_riders
            for p in b.passengers:
                elapsed = p.completed - p.started
                if elapsed > outage_worst[0]:
                    outage_worst = (elapsed, seed, p)
                self.assertLessEqual(elapsed, 510)
            self.assertEqual(len(b.passengers), 120)
        print("v2 initial-load: 2 seeds 41,42; worst %ds seed %s journey %d->%d started %d completed %d" %
              (initial_worst[0], initial_worst[1], initial_worst[2].origin,
               initial_worst[2].destination, initial_worst[2].started,
               initial_worst[2].completed))
        print("v3 randomized-overlap: 2 seeds 41,42; worst %ds seed %s journey %d->%d started %d completed %d; overlap schedules validated" %
              (outage_worst[0], outage_worst[1], outage_worst[2].origin,
               outage_worst[2].destination, outage_worst[2].started,
               outage_worst[2].completed))
        print("v3 measured randomized-overlap eviction coverage: %r" % measured)

    def test_randomized_timing_and_maintenance_families(self):
        """Exercise irregular v2 demand under permanent, temporary and split outages."""
        worst = (0, None)
        v2_worst = (0, None)
        worst_v2_passenger = None
        worst_v3_passenger = None
        for seed in range(18):
            arrivals = make_random_v2_arrivals(3000 + seed)
            healthy = BuildingGroup(Dispatcher(30, 3), arrivals)
            healthy.run(599)
            for p in healthy.passengers:
                elapsed = p.completed - p.started
                if elapsed > v2_worst[0]:
                    v2_worst = (elapsed, seed)
                    worst_v2_passenger = p
                self.assertLessEqual(elapsed, 290,
                    "random v2 seed %d passenger %d->%d took %ds" %
                    (seed, p.origin, p.destination, elapsed))
            if seed % 3 == 0:
                outages = [(0, 0, False)]
            elif seed % 3 == 1:
                start = 80 + seed * 7
                outages = [(start, 1, False), (start + 90, 1, True)]
            else:
                start = 60 + seed * 5
                outages = [(start, 0, False), (start + 40, 0, True),
                           (start + 80, 2, False), (start + 140, 2, True)]
            validate_outages(outages)
            b = BuildingGroup(Dispatcher(30, 3), arrivals, outages)
            b.floors = [0, 15, 29]
            b.run(599)
            self.assertEqual(len(b.passengers), 120)
            for p in b.passengers:
                self.assertIsNotNone(p.completed)
                elapsed = p.completed - p.started
                if elapsed > worst[0]:
                    worst = (elapsed, seed)
                    worst_v3_passenger = p
                self.assertLessEqual(elapsed, 510,
                    "random seed %d passenger %d->%d took %ds" %
                    (seed, p.origin, p.destination, elapsed))
        self.assertLessEqual(worst[0], 510)
        self.assertLessEqual(v2_worst[0], 290)
        p = worst_v2_passenger
        print("v2 randomized sampled worst: %ds seed %s journey %d->%d started %d completed %d" %
              (v2_worst[0], 3000 + v2_worst[1], p.origin, p.destination,
               p.started, p.completed))
        p = worst_v3_passenger
        print("v3 randomized maintenance sampled worst: %ds seed %s journey %d->%d started %d completed %d" %
              (worst[0], 3000 + worst[1], p.origin, p.destination,
               p.started, p.completed))

    def test_group_fixed_cases(self):
        d = Dispatcher(30, 3)
        d.on_call(0, 4, "up")
        commands = d.step(0, [0, 8, 20])
        self.assertEqual(len(commands), 3)
        self.assertEqual(sum(command != "stay" for command in commands), 1)

        # Cars already at the called floor can open together; the call is
        # consumed once and commands remain well formed.
        d = Dispatcher(10, 2)
        d.on_call(0, 3, "up")
        self.assertEqual(d.step(0, [3, 3]), ["open", "stay"])
        self.assertEqual(d.step(1, [3, 3]), ["stay", "stay"])

        # A full car cannot claim the hall stop, but continues its car trip.
        d = Dispatcher(30, 2)
        for _ in range(10):
            d.on_car_request(0, 0, 20)
        d.on_call(0, 5, "up")
        cmds = d.step(0, [0, 29])
        self.assertNotEqual(cmds[0], "open")
        self.assertNotEqual(cmds[1], "open")

    def test_seeded_v2_envelope_and_v1_regression(self):
        worst = (0, None)
        worst_passenger = None
        for seed in range(20):
            arrivals = make_v2_arrivals(seed, seed % 3)
            b = BuildingGroup(Dispatcher(30, 3), arrivals)
            b.run(599)
            for p in b.passengers:
                elapsed = p.completed - p.started
                if elapsed > worst[0]:
                    worst = (elapsed, seed)
                    worst_passenger = p
                self.assertLessEqual(elapsed, 290,
                    "seed %d passenger %d->%d took %ds" %
                    (seed, p.origin, p.destination, elapsed))
            self.assertEqual(len(b.passengers), 120)
        self.assertLessEqual(worst[0], 290)
        p = worst_passenger
        print("v2 fixed: 20 seeds 0-19; worst %ds seed %s journey %d->%d started %d completed %d" %
              (worst[0], worst[1], p.origin, p.destination, p.started, p.completed))

        # Keep the v1 one-car service promise after the dispatcher change.
        group_worst = (0, None, None)
        for seed in range(10):
            b = Building(Dispatcher(30, 1), make_arrivals(seed, clustered=seed % 4 == 0))
            b.run(599)
            for p in b.passengers:
                elapsed = p.completed - p.started
                if elapsed > group_worst[0]:
                    group_worst = (elapsed, seed, p)
                self.assertLessEqual(elapsed, 270)
        p = group_worst[2]
        print("v1 group regression: 10 seeds 0-9; worst %ds seed %s journey %d->%d started %d completed %d" %
              (group_worst[0], group_worst[1], p.origin, p.destination,
               p.started, p.completed))

    def test_v2_rate_validator_rejects_excess(self):
        arrivals = make_v2_arrivals(5)
        arrivals[1] = (arrivals[0][0] + 1, arrivals[1][1], arrivals[1][2], 40)
        with self.assertRaises(AssertionError):
            validate_v2_day(arrivals)


if __name__ == "__main__":
    unittest.main()
