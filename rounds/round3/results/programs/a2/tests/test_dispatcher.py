import random
import unittest

from dispatcher import Dispatcher


VALID = {"up", "down", "stay", "open"}


class DispatcherContractTests(unittest.TestCase):
    def test_interface_and_idle_commands(self):
        d = Dispatcher(30, 1)
        self.assertEqual(d.step(0, [0]), ["stay"])
        self.assertEqual(d.step(1, [29]), ["stay"])
        self.assertEqual(d.step(2, [0]), ["stay"])

    def test_commands_and_boundaries(self):
        d = Dispatcher(3, 1)
        d.on_call(0, 0, "down")
        self.assertEqual(d.step(0, [0]), ["open"])
        d.on_car_request(1, 0, 2)
        self.assertEqual(d.step(1, [0]), ["up"])
        self.assertEqual(d.step(2, [2]), ["open"])
        for n in (1, 2, 30, 37):
            multi = Dispatcher(n, 2)
            cmds = multi.step(0, [0, n - 1])
            self.assertEqual(len(cmds), 2)
            self.assertTrue(set(cmds) <= VALID)

    def test_duplicate_calls_keep_work_and_open_clears_both_directions(self):
        d = Dispatcher(5, 1)
        d.on_call(1, 3, "up")
        d.on_call(100, 3, "up")
        d.on_call(2, 3, "down")
        self.assertEqual(d.step(101, [0]), ["up"])
        self.assertEqual(d.step(102, [3]), ["open"])
        self.assertEqual(d.step(103, [3]), ["stay"])

    def test_recall_after_open_depart_return_and_serve(self):
        d = Dispatcher(6, 1)
        d.on_call(0, 0, "up")
        d.on_call(0, 0, "down")
        self.assertEqual(d.step(0, [0]), ["open"])
        d.on_call(1, 0, "up")
        self.assertEqual(d.step(1, [0]), ["up"])
        self.assertEqual(d.step(2, [1]), ["down"])
        self.assertEqual(d.step(3, [0]), ["open"])
        self.assertEqual(d.step(4, [0]), ["stay"])

    def test_recall_at_top_departures_and_interior(self):
        top = Dispatcher(5, 1)
        top.on_call(0, 4, "down")
        self.assertEqual(top.step(0, [4]), ["open"])
        top.on_call(1, 4, "down")
        self.assertEqual(top.step(1, [4]), ["down"])
        middle = Dispatcher(5, 1)
        middle.on_call(0, 2, "up")
        self.assertEqual(middle.step(0, [2]), ["open"])
        middle.on_call(1, 2, "up")
        command = middle.step(1, [2])[0]
        self.assertIn(command, ("up", "down"))

    def test_recall_coexists_with_onboard_destination(self):
        d = Dispatcher(6, 1)
        d.on_call(0, 0, "up")
        self.assertEqual(d.step(0, [0]), ["open"])
        d.on_car_request(1, 0, 4)
        d.on_call(1, 0, "up")
        self.assertIn(d.step(1, [0])[0], ("up", "open"))
        # The car destination remains actionable after any repeated pickup open.
        floor = 0
        opened_at_destination = False
        for t in range(2, 20):
            cmd = d.step(t, [floor])[0]
            self.assertIn(cmd, VALID)
            if cmd == "up":
                self.assertLess(floor, 5)
                floor += 1
            elif cmd == "down":
                self.assertGreater(floor, 0)
                floor -= 1
            elif cmd == "open" and floor == 4:
                opened_at_destination = True
                break
        self.assertTrue(opened_at_destination)

    def test_repeated_capacity_recall_does_not_starve_onboard_stops(self):
        d = Dispatcher(6, 1)
        d.on_call(0, 0, "up")
        self.assertEqual(d.step(0, [0]), ["open"])
        # Two riders have destinations on opposite sides of an intermediate
        # opening. Re-calls represent people left waiting at the pickup floor.
        d.on_car_request(1, 0, 1)
        d.on_car_request(1, 0, 4)
        d.on_call(1, 0, "up")
        floor = 0
        opened = []
        for t in range(1, 40):
            cmd = d.step(t, [floor])[0]
            if cmd == "up":
                self.assertLess(floor, 5)
                floor += 1
            elif cmd == "down":
                self.assertGreater(floor, 0)
                floor -= 1
            elif cmd == "open":
                opened.append(floor)
                if floor == 1:
                    d.on_call(t + 1, 0, "up")
                if floor == 4:
                    break
        self.assertIn(1, opened)
        self.assertIn(4, opened)

    def test_one_floor_current_floor_service(self):
        d = Dispatcher(1, 1)
        d.on_call(0, 0, "up")
        self.assertEqual(d.step(0, [0]), ["open"])
        d.on_call(1, 0, "down")
        self.assertEqual(d.step(1, [0]), ["open"])
        self.assertEqual(d.step(2, [0]), ["stay"])

    def test_invalid_events_and_observations_are_safe(self):
        d = Dispatcher(5, 2)
        for args in ((None, 1, "up"), (-1, 1, "up"), (1, 8, "up"),
                     (1, 1, "side"), (True, 1, "up")):
            d.on_call(*args)
        for args in ((0, 2, 2), (0, -1, 2), (None, 0, 1), (0, 0, 9)):
            d.on_car_request(*args)
        self.assertEqual(d.step(0, [0]), ["stay", "stay"])
        self.assertEqual(d.step(0, [0, 5]), ["stay", "stay"])
        self.assertEqual(d.step(0, None), ["stay", "stay"])


def make_day(seed, crowd_size=12, random_crowd_origin=False):
    """Generate 40 trips in ticks 0..599 under all rolling arrival caps."""
    if type(crowd_size) is not int or not 0 <= crowd_size <= 12:
        raise ValueError("crowd_size must be between 0 and 12")
    rng = random.Random(seed)
    crowd_t = rng.randrange(120) if crowd_size else None
    arrivals = [(crowd_t, True) for _ in range(crowd_size)]
    while len(arrivals) < 40:
        t = rng.randrange(600)
        candidate = sorted([at for at, _ in arrivals] + [t])
        # Any closed 10, 60, or 300 tick window must satisfy the stated cap.
        if any(sum(x <= end and x > end - width for x in candidate) > cap
               for end in candidate for width, cap in ((10, 15), (60, 20), (300, 35))):
            continue
        arrivals.append((t, False))
    arrivals.sort(key=lambda item: item[0])
    trips = []
    for i, (t, crowd) in enumerate(arrivals):
        origin = rng.randrange(30) if (not crowd or random_crowd_origin) else 12
        dest = rng.randrange(29)
        if dest >= origin:
            dest += 1
        trips.append({"id": i, "time": t, "origin": origin, "dest": dest,
                      "start": t, "boarded": False, "done": False,
                      "crowd": crowd})
    validate_schedule(trips)
    return trips


def validate_schedule(trips):
    assert len(trips) == 40
    assert all(0 <= p["time"] < 600 and p["dest"] != p["origin"] for p in trips)
    assert all(type(p["crowd"]) is bool for p in trips)
    crowd = [p for p in trips if p["crowd"]]
    assert 0 <= len(crowd) <= 12
    if crowd:
        assert len({p["time"] for p in crowd}) == 1
    timestamps = sorted(p["time"] for p in trips)
    for width, cap in ((10, 15), (60, 20), (300, 35)):
        for end in timestamps:
            assert sum(end - width < t <= end for t in timestamps) <= cap


def simulate(seed, initially_aboard=False, crowd_size=12, random_crowd_origin=False):
    trips = make_day(seed, crowd_size, random_crowd_origin)
    d = Dispatcher(30, 1)
    waiting, onboard, delivered = {}, [], []
    if initially_aboard:
        # One of the 40 trips starts aboard; it is not an extra passenger.
        p = next(p for p in reversed(trips) if p["dest"] != 0)
        trips.remove(p)
        p.update(time=0, origin=0, start=0, boarded=True)
        onboard.append(p)
        d.on_car_request(0, 0, p["dest"])
        trips.append(p)
        validate_schedule(trips)
    by_time, car_events, hall_events = {}, {}, {}
    aboard_ids = {p["id"] for p in onboard}
    for p in trips:
        if p["id"] not in aboard_ids:
            by_time.setdefault(p["time"], []).append(p)
    floor = 0
    for t in range(12000):
        for lift, target in car_events.pop(t, []):
            d.on_car_request(t, lift, target)
        for f, direction in hall_events.pop(t, []):
            d.on_call(t, f, direction)
        for p in by_time.get(t, []):
            waiting.setdefault(p["origin"], []).append(p)
            d.on_call(t, p["origin"], "up" if p["dest"] > p["origin"] else "down")
        cmd = d.step(t, [floor])
        assert len(cmd) == 1 and cmd[0] in VALID, (t, floor, cmd)
        action = cmd[0]
        if action == "up":
            assert floor < 29
            floor += 1
        elif action == "down":
            assert floor > 0
            floor -= 1
        elif action == "open":
            keep = []
            for p in onboard:
                if p["dest"] == floor:
                    p["done"], p["finish"] = True, t
                    delivered.append(p)
                else:
                    keep.append(p)
            onboard = keep
            queue = waiting.get(floor, [])
            space = 10 - len(onboard)
            boarded = queue[:space]
            for p in boarded:
                p["boarded"] = True
                onboard.append(p)
                car_events.setdefault(t + 1, []).append((0, p["dest"]))
            waiting[floor] = queue[len(boarded):]
            if waiting[floor]:
                # The repeated hall press represents only those left waiting.
                dirs = {"up" if p["dest"] > floor else "down" for p in waiting[floor]}
                for direction in dirs:
                    hall_events.setdefault(t + 1, []).append((floor, direction))
        if len(delivered) == 40:
            break
    if len(delivered) != 40:
        pending = sum(map(len, waiting.values())) + len(onboard)
        raise AssertionError(f"seed {seed}: only {len(delivered)}/40 delivered; pending={pending}")
    elapsed = [p["finish"] - p["start"] for p in delivered]
    assert len(elapsed) == 40
    return max(elapsed), elapsed


class EnvelopeSimulationTests(unittest.TestCase):
    def test_generator_tags_equal_time_crowds_and_enforces_caps(self):
        for size in range(1, 13):
            for seed in range(20):
                trips = make_day(seed + 5000, crowd_size=size)
                self.assertEqual(sum(p["crowd"] for p in trips), size)
                validate_schedule(trips)

    def test_reproducible_envelope_days_meet_per_passenger_limit(self):
        # 100 ordinary random days and 100 explicit crowd days, spanning sizes 1..12.
        cases = [(seed, 0, 12) for seed in range(100)]
        cases += [(1000 + seed, 1, seed % 12 + 1) for seed in range(100)]
        self._check_cohort("acceptance", cases)

    def test_complementary_random_origin_and_crowd_free_days(self):
        random_origin = [(2000 + seed, False, 12, True) for seed in range(50)]
        crowd_free = [(3000 + seed, False, 0, False) for seed in range(50)]
        sampled_origins = {
            p["origin"] for seed, _, size, _ in random_origin
            for p in make_day(seed, size, random_crowd_origin=True) if p["crowd"]
        }
        self.assertIn(0, sampled_origins)
        self.assertIn(29, sampled_origins)
        self._check_cohort("random crowd origins", random_origin)
        self._check_cohort("crowd free", crowd_free)

    def _check_cohort(self, label, cases):
        results, failures = [], []
        for case in cases:
            seed, initially_aboard, crowd_size, *extra = case
            random_origin = extra[0] if extra else False
            try:
                maximum, elapsed = simulate(seed, bool(initially_aboard), crowd_size,
                                           random_crowd_origin=random_origin)
                results.append((seed, maximum, len(elapsed)))
                if maximum > 270:
                    failures.append((seed, f"deadline {maximum}s"))
            except Exception as exc:
                failures.append((seed, str(exc)))
        max_time = max((m for _, m, _ in results), default=None)
        print(f"v1 {label}: days={len(cases)}, complete={len(results)}/{len(cases)}, "
              f"max={max_time}s, failures={failures}")
        self.assertEqual(len(results), len(cases), f"incomplete days: {failures}")
        self.assertEqual(failures, [])

    def test_initially_aboard_trip_counts_from_zero(self):
        maximum, times = simulate(81, initially_aboard=True)
        self.assertEqual(len(times), 40)
        self.assertLessEqual(maximum, 270)


# V2 uses a separate three-car simulator so the v1 envelope and its assertions
# remain unchanged. A trip is one passenger; capacity re-calls are events only.
def make_v2_day(seed, kind="random", crowd_size=15, initially_aboard=False):
    rng = random.Random(seed)
    arrivals = []
    crowd_t = rng.randrange(120) if kind == "crowd" else None
    if kind == "crowd":
        arrivals.extend([crowd_t] * crowd_size)
    elif kind == "burst":
        burst_t = rng.randrange(120)
        arrivals.extend([burst_t + i % 10 for i in range(30)])
    while len(arrivals) < 120:
        t = rng.randrange(600)
        candidate = sorted(arrivals + [t])
        if any(sum(end - width < x <= end for x in candidate) > cap
               for end in candidate for width, cap in ((10, 35), (60, 50), (300, 90))):
            continue
        arrivals.append(t)
    trips = []
    crowd_origin = (0 if seed % 2 == 0 else 29) if kind == "crowd" else None
    for i, t in enumerate(arrivals):
        is_crowd = kind == "crowd" and t == crowd_t and i < crowd_size
        origin = crowd_origin if is_crowd else rng.randrange(30)
        dest = rng.randrange(29)
        if dest >= origin:
            dest += 1
        trips.append(dict(id=i, time=t, origin=origin, dest=dest, start=t,
                          boarded=False, done=False, crowd=is_crowd))
    if initially_aboard:
        for lift in range(3):
            p = next(p for p in reversed(trips) if "aboard_lift" not in p and p["dest"] != 0)
            trips.remove(p)
            p.update(time=0, origin=0, start=0, boarded=True, aboard_lift=lift)
            trips.append(p)
    validate_v2_schedule(trips)
    return trips


def validate_v2_schedule(trips):
    assert len(trips) == 120 and len({p["id"] for p in trips}) == 120
    assert all(0 <= p["time"] < 600 and 0 <= p["origin"] < 30 and
               0 <= p["dest"] < 30 and p["dest"] != p["origin"] for p in trips)
    timestamps = sorted(p["time"] for p in trips if "aboard_lift" not in p)
    for width, cap in ((10, 35), (60, 50), (300, 90)):
        for end in timestamps:
            assert sum(end - width < t <= end for t in timestamps) <= cap
    crowds = [p for p in trips if p["crowd"]]
    if crowds:
        assert len(crowds) <= 15 and len({(p["time"], p["origin"]) for p in crowds}) == 1


def simulate_v2(seed, kind="random", crowd_size=15, initially_aboard=False,
                outages=None):
    trips = make_v2_day(seed, kind, crowd_size, initially_aboard)
    d = Dispatcher(30, 3)
    floors = [0, 0, 0]
    onboard = [[], [], []]
    waiting = {}
    delivered = []
    car_events, hall_events, by_time = {}, {}, {}
    for p in trips:
        if p.get("aboard_lift") is not None:
            lift = p["aboard_lift"]
            onboard[lift].append(p)
            d.on_car_request(0, lift, p["dest"])
        else:
            by_time.setdefault(p["time"], []).append(p)
    trace = []
    outages = outages or {}
    available = [True] * 3
    for t in range(18000):
        for lift, target in car_events.pop(t, []): d.on_car_request(t, lift, target)
        for f, direction in hall_events.pop(t, []): d.on_call(t, f, direction)
        for p in by_time.get(t, []):
            waiting.setdefault(p["origin"], []).append(p)
            d.on_call(t, p["origin"], "up" if p["dest"] > p["origin"] else "down")
        # Outages are half-open intervals. Evacuation happens before service;
        # transferred riders keep their original start time.
        for i, (off, ret) in outages.items():
            if t == off:
                available[i] = False
                d.set_lift_available(t, i, False)
                keep = []
                for p in onboard[i]:
                    if p["dest"] == floors[i]:
                        p.update(done=True, finish=t)
                        delivered.append(p)
                    else:
                        p["boarded"] = False
                        waiting.setdefault(floors[i], []).append(p)
                        d.on_call(t, floors[i], "up" if p["dest"] > floors[i] else "down")
                onboard[i] = keep
            if ret is not None and t == ret:
                available[i] = True
                d.set_lift_available(t, i, True)
        cmds = d.step(t, list(floors))
        assert len(cmds) == 3 and set(cmds) <= VALID, (t, floors, cmds)
        for i in range(3):
            if not available[i]:
                assert cmds[i] == "stay", (t, i, cmds)
        for i, (f, cmd) in enumerate(zip(floors, cmds)):
            if cmd == "up": assert f < 29, (t, i, f, cmd)
            if cmd == "down": assert f > 0, (t, i, f, cmd)
        # Drop offs are per car; simultaneous openings board in lift index order.
        openings = [i for i, cmd in enumerate(cmds) if cmd == "open"]
        for i in openings:
            remain = []
            for p in onboard[i]:
                if p["dest"] == floors[i]:
                    p.update(done=True, finish=t)
                    delivered.append(p)
                else: remain.append(p)
            onboard[i] = remain
        for i in openings:
            queue = waiting.get(floors[i], [])
            space = 10 - len(onboard[i])
            boarded = queue[:space]
            for p in boarded:
                p["boarded"] = True
                onboard[i].append(p)
                car_events.setdefault(t + 1, []).append((i, p["dest"]))
            waiting[floors[i]] = queue[len(boarded):]
        for floor, queue in waiting.items():
            if queue and any(floors[i] == floor for i in openings):
                for direction in {"up" if p["dest"] > floor else "down" for p in queue}:
                    hall_events.setdefault(t + 1, []).append((floor, direction))
        trace.append((t, tuple(floors), tuple(cmds)))
        for i, cmd in enumerate(cmds):
            if cmd == "up": floors[i] += 1
            elif cmd == "down": floors[i] -= 1
        if len(delivered) == len(trips): break
    elapsed = [(p["finish"] - p["start"], p) for p in delivered]
    overdue = [(dt, p) for dt, p in elapsed if dt > 290]
    return dict(expected=len(trips), delivered=len(delivered), elapsed=elapsed,
                overdue=overdue, trace=trace, pending=sum(map(len, waiting.values())) + sum(map(len, onboard)))


class V2EnvelopeSimulationTests(unittest.TestCase):
    def test_v2_focused_contract(self):
        d = Dispatcher(30, 3)
        self.assertEqual(d.step(0, [0, 29, 15]), ["stay"] * 3)
        d.on_car_request(0, 1, 28)
        self.assertEqual(d.step(1, [0, 29, 15])[1], "down")
        for f, direction in ((0, "up"), (29, "down"), (15, "up")):
            d.on_call(2, f, direction)
        cmds = d.step(2, [0, 29, 15])
        self.assertEqual(len(cmds), 3)
        self.assertTrue(set(cmds) <= VALID)
        for seed in range(30):
            for kind in ("random", "crowd", "burst"):
                validate_v2_schedule(make_v2_day(seed, kind, seed % 15 + 1))

    def test_v2_sampled_days(self):
        cases = [(seed, "random", 15, seed % 12 == 0) for seed in range(100)]
        cases += [(1000 + seed, "crowd", seed % 15 + 1, seed % 10 == 0) for seed in range(100)]
        cases += [(2000 + seed, "burst", 15, seed % 10 == 0) for seed in range(100)]
        failures, maximum = [], 0
        for seed, kind, size, aboard in cases:
            result = simulate_v2(seed, kind, size, aboard)
            maximum = max(maximum, max((x[0] for x in result["elapsed"]), default=0))
            if result["delivered"] != result["expected"] or result["overdue"]:
                failures.append((seed, kind, result["delivered"], result["expected"],
                                 [(dt, p["id"], p["origin"], p["dest"]) for dt, p in result["overdue"]],
                                 result["pending"], result["trace"][-10:]))
        print(f"v2: days={len(cases)}, max={maximum}s, failures={failures}")
        self.assertEqual(failures, [])


def validate_outages(outages, run_end=18000):
    assert len(outages) <= 2
    intervals = []
    for lift, (off, ret) in outages.items():
        assert lift in range(3) and type(off) is int and off >= 0
        assert ret is None or (type(ret) is int and ret > off)
        intervals.append((off, run_end if ret is None else ret, lift))
    for t in range(run_end):
        offline = [i for a, b, i in intervals if a <= t < b]
        assert len(offline) < 3
    overlap = sum(sum(a <= t < b for a, b, _ in intervals) == 2
                  for t in range(run_end))
    assert overlap <= 120


class V3MaintenanceTests(unittest.TestCase):
    def test_initial_occupancy_fixture_has_three_distinct_cars_at_real_floors(self):
        trips = make_v2_day(81, initially_aboard=True)
        aboard = [p for p in trips if "aboard_lift" in p]
        self.assertEqual({p["aboard_lift"] for p in aboard}, {0, 1, 2})
        self.assertEqual(len(aboard), 3)
        self.assertTrue(all(p["origin"] == 0 and p["time"] == p["start"] == 0
                            for p in aboard))

    def test_outage_schedules_and_lifecycle_acceptance(self):
        schedules = [
            {0: (0, None)}, {1: (90, 220)}, {2: (10, 160), 0: (80, 200)},
            {1: (0, 120), 2: (30, 150)}, {2: (40, 160), 1: (300, None)},
        ]
        for schedule in schedules:
            validate_outages(schedule)
        # Exercise permanent loss, return without re-sending calls, evacuation,
        # and overlapping outages while retaining the v2 passenger clocks.
        for seed, schedule in enumerate(schedules):
            result = simulate_v2(800 + seed, "random", 15, True, schedule)
            self.assertEqual(result["delivered"], result["expected"])
            self.assertEqual(result["overdue"], [])


class V4FireModeTests(unittest.TestCase):
    def test_fire_commands_descend_open_ground_and_hold_outage(self):
        d = Dispatcher(30, 3)
        d.on_car_request(0, 0, 18)
        d.on_call(0, 23, "down")
        d.set_mode(60, "fire")
        self.assertEqual(d.step(60, [0, 12, 29]), ["open", "down", "down"])
        self.assertEqual(d.step(61, [0, 11, 28]), ["open", "down", "down"])
        d.set_lift_available(62, 1, False)
        self.assertEqual(d.step(62, [0, 10, 27]), ["open", "stay", "down"])
        self.assertEqual(d.step(70, [0, 0, 0]), ["open", "stay", "open"])

    def test_fire_opening_discards_old_car_calls_and_normal_replays_hall(self):
        d = Dispatcher(5, 1)
        d.on_car_request(0, 0, 4)
        d.on_call(0, 3, "up")
        d.set_mode(60, "fire")
        self.assertEqual(d.step(60, [1]), ["down"])
        self.assertEqual(d.step(61, [0]), ["open"])
        # A late car notification after evacuation must not resurrect a trip.
        d.on_car_request(62, 0, 4)
        d.on_call(62, 3, "down")
        d.set_mode(70, "normal")
        self.assertEqual(d.step(70, [0]), ["up"])
        self.assertEqual(d.step(71, [1]), ["up"])
        self.assertEqual(d.step(72, [2]), ["up"])
        self.assertEqual(d.step(73, [3]), ["open"])

    def test_invalid_mode_is_harmless_and_fire_can_end(self):
        d = Dispatcher(3, 1)
        d.set_mode(0, "water")
        d.on_car_request(0, 0, 2)
        self.assertEqual(d.step(0, [0]), ["up"])
        d.set_mode(1, "fire")
        self.assertEqual(d.step(1, [1]), ["down"])
        d.set_mode(2, "normal")
        self.assertEqual(d.step(2, [0]), ["up"])

    def test_returning_lift_gets_full_fire_return_allowance(self):
        d = Dispatcher(8, 2)
        d.set_lift_available(1, 1, False)
        d.set_mode(2, "fire")
        d.set_lift_available(3, 1, True)
        # An empty returning lift still follows the mandatory fire route.
        self.assertEqual(d.step(3, [0, 7]), ["open", "down"])
        self.assertEqual(d.step(9, [0, 1]), ["open", "down"])
        self.assertEqual(d.step(10, [0, 0]), ["open", "open"])
        self.assertEqual(d.step(11, [0, 0]), ["open", "open"])

    def test_fire_keeps_non_evacuated_car_work_if_mode_ends_early(self):
        d = Dispatcher(6, 1)
        d.on_car_request(0, 0, 4)
        d.set_mode(1, "fire")
        self.assertEqual(d.step(1, [2]), ["down"])
        d.set_mode(2, "normal")
        self.assertEqual(d.step(2, [1]), ["up"])


class V5MorningRushTests(unittest.TestCase):
    def test_v5_schedule_and_passenger_acceptance(self):
        # The 25/60 cap is for trips whose origin is above the lobby.
        maxima = []
        for seed in range(12):
            trips = make_v5_day(seed)
            validate_v5_schedule(trips)
            result = simulate_v5(trips)
            self.assertEqual(result["delivered"], 300)
            self.assertEqual(result["pending"], 0)
            lobby = sorted(dt for dt, p in result["elapsed"] if p["origin"] == 0)
            upstairs = [dt for dt, p in result["elapsed"] if p["origin"] != 0]
            self.assertLessEqual(lobby[227], 1760, (seed, lobby[227]))
            self.assertLessEqual(max(upstairs), 190, (seed, max(upstairs)))
            self.assertLessEqual(max(dt for dt, _ in result["elapsed"]), 1850)
            maxima.append((lobby[227], max(upstairs), max(dt for dt, _ in result["elapsed"])))
        print(f"v5: days=12, max lobby p95={max(x[0] for x in maxima)}s, "
              f"max upstairs={max(x[1] for x in maxima)}s, max overall={max(x[2] for x in maxima)}s")


def make_v5_day(seed):
    """Construct 300 varied trips with valid rolling arrival limits."""
    rng = random.Random(seed)
    # One passenger per tick is well inside both total arrival caps. Every
    # fifth origin is upstairs (60 total); all other trips start in the lobby.
    trips = []
    for i in range(300):
        t = i
        if i % 5 == 0:
            origin = rng.randrange(1, 30)
            dest = 0 if rng.random() < .5 else rng.choice([f for f in range(1, 30) if f != origin])
        else:
            origin = 0
            dest = rng.randrange(1, 30)
        trips.append(dict(id=i, time=t, origin=origin, dest=dest, start=t))
    return trips


def validate_v5_schedule(trips):
    assert len(trips) == 300 and len({p["id"] for p in trips}) == 300
    assert sum(p["origin"] == 0 for p in trips) == 240
    assert sum(p["origin"] != 0 for p in trips) == 60
    assert all(0 <= p["time"] < 300 and 0 <= p["origin"] < 30 and
               0 <= p["dest"] < 30 and p["origin"] != p["dest"] for p in trips)
    crowd = {}
    for p in trips:
        crowd[p["time"], p["origin"]] = crowd.get((p["time"], p["origin"]), 0) + 1
    assert max(crowd.values()) <= 6
    for width, cap in ((10, 25), (60, 85)):
        for end in range(300):
            assert sum(end - width < p["time"] <= end for p in trips) <= cap
    for end in range(300):
        assert sum(end - 60 < p["time"] <= end and p["origin"] != 0
                   for p in trips) <= 25


def simulate_v5(trips):
    d = Dispatcher(30, 3)
    floors, onboard, waiting = [0, 0, 0], [[], [], []], {}
    car_events, hall_events, by_time = {}, {}, {}
    for p in trips: by_time.setdefault(p["time"], []).append(p)
    delivered, elapsed = [], []
    for t in range(2150):
        for i, f in car_events.pop(t, []): d.on_car_request(t, i, f)
        for f, direction in hall_events.pop(t, []): d.on_call(t, f, direction)
        for p in by_time.get(t, []):
            waiting.setdefault(p["origin"], []).append(p)
            d.on_call(t, p["origin"], "up" if p["dest"] > p["origin"] else "down")
        cmds = d.step(t, floors[:])
        assert len(cmds) == 3 and set(cmds) <= VALID
        assert all(not (c == "up" and floors[i] == 29) and
                   not (c == "down" and floors[i] == 0) for i, c in enumerate(cmds))
        openings = [i for i, c in enumerate(cmds) if c == "open"]
        for i in openings:
            remain = []
            for p in onboard[i]:
                if p["dest"] == floors[i]:
                    p["finish"] = t
                    elapsed.append((t - p["start"], p))
                else: remain.append(p)
            onboard[i] = remain
        for i in openings:
            q = waiting.get(floors[i], [])
            boarded = q[:10-len(onboard[i])]
            for p in boarded:
                onboard[i].append(p)
                car_events.setdefault(t+1, []).append((i, p["dest"]))
            waiting[floors[i]] = q[len(boarded):]
        for f, q in waiting.items():
            if q and any(floors[i] == f for i in openings):
                for direction in {"up" if p["dest"] > f else "down" for p in q}:
                    hall_events.setdefault(t+1, []).append((f, direction))
        for i, c in enumerate(cmds):
            if c == "up": floors[i] += 1
            elif c == "down": floors[i] -= 1
        if len(elapsed) == 300: break
    return {"delivered": len(elapsed), "pending": sum(map(len, waiting.values())) + sum(map(len, onboard)),
            "elapsed": elapsed}


def simulate_v4(seed, fire, outages=None):
    """Simulate one v2-envelope day with fire evacuation and maintenance."""
    trips = make_v2_day(seed, "random", 15, initially_aboard=True)
    d = Dispatcher(30, 3)
    floors = [0, 0, 0]
    onboard, waiting, delivered, evacuated = [[], [], []], {}, [], []
    car_events, hall_events, by_time = {}, {}, {}
    for p in trips:
        if p.get("aboard_lift") is not None:
            i = p["aboard_lift"]
            onboard[i].append(p)
            d.on_car_request(0, i, p["dest"])
        else:
            by_time.setdefault(p["time"], []).append(p)
    outages = outages or {}
    validate_outages(outages)
    available = [True] * 3
    fire_start, fire_end = fire
    fire_active = False
    for t in range(18000):
        for i, target in car_events.pop(t, []): d.on_car_request(t, i, target)
        for f, direction in hall_events.pop(t, []): d.on_call(t, f, direction)
        for p in by_time.get(t, []):
            waiting.setdefault(p["origin"], []).append(p)
            d.on_call(t, p["origin"], "up" if p["dest"] > p["origin"] else "down")
        if t == fire_start:
            fire_active = True
            d.set_mode(t, "fire")
        for i, (off, ret) in outages.items():
            if t == off:
                available[i] = False
                d.set_lift_available(t, i, False)
                for p in onboard[i]:
                    if p["dest"] == floors[i]:
                        p.update(done=True, finish=t); delivered.append(p)
                    else:
                        p["boarded"] = False
                        waiting.setdefault(floors[i], []).append(p)
                        d.on_call(t, floors[i], "up" if p["dest"] > floors[i] else "down")
                onboard[i] = []
            if ret is not None and t == ret:
                available[i] = True
                d.set_lift_available(t, i, True)
        if t == fire_end:
            fire_active = False
            d.set_mode(t, "normal")
            for f, queue in waiting.items():
                for direction in {"up" if p["dest"] > f else "down" for p in queue}:
                    d.on_call(t, f, direction)
        cmds = d.step(t, list(floors))
        assert len(cmds) == 3 and set(cmds) <= VALID
        for i, cmd in enumerate(cmds):
            if not available[i]: assert cmd == "stay"
            if cmd == "up": assert floors[i] < 29
            if cmd == "down": assert floors[i] > 0
        openings = [i for i, cmd in enumerate(cmds) if cmd == "open"]
        for i in openings:
            remain = []
            for p in onboard[i]:
                if fire_active and floors[i] == 0:
                    p["evacuated"] = True
                    evacuated.append(p)
                elif not fire_active and p["dest"] == floors[i]:
                    p.update(done=True, finish=t); delivered.append(p)
                else: remain.append(p)
            onboard[i] = remain
        if not fire_active:
            for i in openings:
                queue = waiting.get(floors[i], [])
                boarded = queue[:max(0, 10 - len(onboard[i]))]
                for p in boarded:
                    p["boarded"] = True
                    onboard[i].append(p)
                    car_events.setdefault(t + 1, []).append((i, p["dest"]))
                waiting[floors[i]] = queue[len(boarded):]
            for f, queue in waiting.items():
                if queue and any(floors[i] == f for i in openings):
                    for direction in {"up" if p["dest"] > f else "down" for p in queue}:
                        hall_events.setdefault(t + 1, []).append((f, direction))
        for i, cmd in enumerate(cmds):
            if cmd == "up": floors[i] += 1
            elif cmd == "down": floors[i] -= 1
        if len(delivered) + len(evacuated) == len(trips): break
    elapsed = [(p["finish"] - p["start"], p) for p in delivered]
    return dict(expected=len(trips), delivered=len(delivered), evacuated=len(evacuated),
                elapsed=elapsed, overdue=[x for x in elapsed if x[0] > 590],
                pending=len(trips) - len(delivered) - len(evacuated))


class V4PassengerAcceptanceTests(unittest.TestCase):
    def test_fire_and_fire_with_maintenance_sampled_days(self):
        cases = [
            (4100, (100, 140), {}),
            (4101, (60, 180), {0: (80, 150)}),
            (4102, (479, 500), {1: (40, 160), 2: (100, 180)}),
            (4103, (200, 260), {0: (0, None)}),
            (4104, (300, 420), {1: (250, 390)}),
        ]
        for seed, fire, outages in cases:
            with self.subTest(seed=seed, fire=fire, outages=outages):
                result = simulate_v4(seed, fire, outages)
                self.assertEqual(result["delivered"] + result["evacuated"], result["expected"])
                self.assertEqual(result["pending"], 0)
                self.assertEqual(result["overdue"], [])

    def test_fire_can_evacuate_every_onboard_rider_without_counting_them(self):
        result = simulate_v4(512, (60, 90))
        self.assertGreater(result["evacuated"], 0)
        self.assertEqual(result["overdue"], [])


if __name__ == "__main__":
    unittest.main()
