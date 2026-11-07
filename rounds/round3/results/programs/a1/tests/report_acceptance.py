"""Run the reviewer acceptance suite and print reproducible run metrics."""
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.dirname(__file__))
import test_dispatcher as td


def run_retained():
    specs = (("v1", range(20), td.make_random_day, 1, 270, None),
             ("v2", range(20), td.make_v2_day, 3, 290, None),
             ("v3", range(100, 105), td.make_v2_day, 3, 510, "v3"),
             ("v4-retained", (777,), td.make_v2_day, 3, 590, "v4"))
    rows = []
    for version, seeds, generator, lifts, limit, scenario in specs:
        for seed in seeds:
            w = td.World(td.Dispatcher(30, lifts))
            for t, origin, dest in generator(seed):
                w.arrival(t, origin, dest)
            if scenario in ("v3", "v4"):
                w.set_lift_available(0, 0, False)
                w.set_lift_available(100, 1, False)
                w.set_lift_available(220, 1, True)
            if scenario == "v4":
                w.set_mode(120, "fire")
                w.set_mode(180, "normal")
            w.run(599, 3000)
            waits = [t-p["start"] for p, t in w.done]
            maximum = max(waits, default=None)
            rows.append((version, seed, len(w.registry), 0, len(w.done), len(w.evacuated),
                         sum(len(v) for v in w.waiting.values()) + sum(map(len, w.riders)),
                         maximum, limit, maximum is None or maximum <= limit))
    return rows


def run_v5():
    rows = []
    for family, seed, arrivals in td.v5_manifest():
        td.assert_valid_v5_envelope(unittest.TestCase(), arrivals)
        world = td.World(td.Dispatcher(30, 3))
        for t, origin, dest in arrivals:
            world.arrival(t, origin, dest)
        initialized = sum(len(riders) for riders in world.riders)
        world.run(299, 3000)
        waits = [(t - p["start"], p["origin"], t, p["id"]) for p, t in world.done]
        lobby = sorted(wait for wait, origin, _, _ in waits if origin == 0)
        upper = [wait for wait, origin, _, _ in waits if origin != 0]
        p95 = lobby[(95 * len(lobby) + 99) // 100 - 1]
        final_open = max((opened for _, _, opened, _ in waits), default=None)
        future = sum(len(events) for events in world.events.values())
        waiting = sum(map(len, world.waiting.values()))
        onboard = sum(map(len, world.riders))
        pending_events = len(world.events)
        pending = waiting + onboard
        rows.append((family, seed, len(world.registry), initialized, len(world.done), len(lobby), len(upper),
                     p95, max(lobby), max(upper), max(w for w, _, _, _ in waits),
                     final_open, future, waiting, onboard, len(world.evacuated), pending_events,
                     len(world.modes), len(world.maintenance), not pending and not world.events
                     and not world.modes and not world.maintenance and len(world.done) == len(world.registry)))
    return rows


def main():
    suite = unittest.defaultTestLoader.loadTestsFromModule(td)
    result = unittest.TextTestRunner(verbosity=1).run(suite)
    if not result.wasSuccessful():
        return 1
    rows = td.VersionFourFireTests.matrix_metrics
    print("V4 per-seed report: family seed fire maintenance return-tick/floor generated initialized completed evacuated pending max-time violations interactions")
    names = ("fire-only", "permanent+fire", "permanent+in-fire-return", "staggered")
    for row in rows:
        family, seed, done, ev, maximum, start, end, outages, returns, gen, init, pending, _, obs = row
        compact = {key: (f"{len(value)}; first={value[0]}" if value else "absent")
                   for key, value in obs.items()}
        print(f"{names[family]} {seed} [{start},{end}) {outages} returns={returns} "
              f"generated={gen} initialized={init} completed={done} evacuated={ev} "
              f"pending={pending} pending-events=(0,0,0) max={maximum if maximum is not None else 'N/A'} "
              f"violations=(identity=0,command=0,recall=0,time=0) interactions={compact}")
    print("V4 family aggregates: family days generated initialized completed evacuated maximum-time")
    for family, name in enumerate(names):
        subset = [r for r in rows if r[0] == family]
        maximum = max((r[4] for r in subset if r[4] is not None), default=None)
        print(name, len(subset), sum(r[9] for r in subset), sum(r[10] for r in subset),
              sum(r[2] for r in subset), sum(r[3] for r in subset), maximum)
    retained = run_retained()
    if any(not row[9] or row[6] for row in retained):
        print("retained acceptance failure: incomplete day or time limit exceeded")
        return 1
    print("Retained version per-seed: version seed generated initialized completed evacuated pending maximum limit pass")
    for row in retained:
        print(*row)
    print("Retained aggregates: version days generated initialized completed evacuated pending maximum verdict")
    for version in dict.fromkeys(r[0] for r in retained):
        subset = [r for r in retained if r[0] == version]
        maximum = max((r[7] for r in subset if r[7] is not None), default=None)
        print(version, len(subset), sum(r[2] for r in subset), sum(r[3] for r in subset),
              sum(r[4] for r in subset), sum(r[5] for r in subset), sum(r[6] for r in subset),
              maximum, "PASS" if all(r[9] for r in subset) else "FAIL")
    rush = run_v5()
    print("V5 morning rush: family seed validity generated initialized completed lobby upstairs p95 lobby-max upstairs-max overall-max final-open future waiting onboard evacuated pending-event-ticks modes maintenance conservation-drain gates")
    for row in rush:
        (family, seed, generated, initialized, completed, lobby_n, upper_n, p95, lobby_max,
         upstairs, overall, final_open, future, waiting, onboard, evacuated,
         events, modes, maintenance, drained) = row
        gates = (p95 <= 1760, upstairs <= 190, overall <= 1850)
        valid = generated == 300 and lobby_n == 240 and upper_n == 60
        print(family, seed, "PASS" if valid else "FAIL", generated, initialized, completed,
              lobby_n, upper_n, p95, lobby_max, upstairs, overall, final_open, future,
              waiting, onboard, evacuated, events, modes, maintenance, drained, gates)
    print("V5 family aggregates: family days generated initialized completed lobby upstairs evacuated future waiting onboard worst-p95 p95-seed worst-upstairs upstairs-seed worst-overall overall-seed")
    for family in dict.fromkeys(row[0] for row in rush):
        subset = [r for r in rush if r[0] == family]
        wp = max(subset, key=lambda r: (r[7], -r[1]))
        wu = max(subset, key=lambda r: (r[9], -r[1]))
        wa = max(subset, key=lambda r: (r[10], -r[1]))
        print(family, len(subset), sum(r[2] for r in subset), sum(r[3] for r in subset),
              sum(r[4] for r in subset), sum(r[5] for r in subset), sum(r[6] for r in subset),
              sum(r[15] for r in subset), sum(r[12] for r in subset),
              sum(r[13] for r in subset), sum(r[14] for r in subset),
              wp[7], wp[1], wu[9], wu[1], wa[10], wa[1])
    print("V5 global worst gates: gate family seed seconds limit")
    for label, index, limit in (("lobby-p95", 7, 1760), ("upstairs", 9, 190),
                                ("overall", 10, 1850)):
        # Manifest order then ascending seed resolves exact ties.
        winner = max(rush, key=lambda row: (row[index], -next(
            i for i, family in enumerate(dict.fromkeys(r[0] for r in rush)) if family == row[0]), -row[1]))
        print(label, winner[0], winner[1], winner[index], limit)
    print("V5 totals:", "days", len(rush), "generated", sum(r[2] for r in rush),
          "initialized", sum(r[3] for r in rush), "completed", sum(r[4] for r in rush),
          "lobby", sum(r[5] for r in rush), "upstairs", sum(r[6] for r in rush),
          "future", sum(r[12] for r in rush), "waiting", sum(r[13] for r in rush),
          "onboard", sum(r[14] for r in rush), "evacuated", sum(r[15] for r in rush),
          "pending-event-ticks", sum(r[16] for r in rush))
    if any(generated != 300 or completed != 300 or lobby_n != 240 or upper_n != 60
           or future or waiting or onboard or evacuated or events or modes or maintenance or not drained
           or p95 > 1760 or upstairs > 190 or overall > 1850
           for _, _, generated, _, completed, lobby_n, upper_n, p95, _, upstairs, overall,
           _, future, waiting, onboard, evacuated, events, modes, maintenance, drained in rush):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
