"""Hand-built days inside the stated envelope, the hardest arrangements we could write: every call as early as the
caps allow, with the destinations and origins that cost a lift the most. The audit's shuttle probe is the first
pattern. Run as a script for the table; calibrate_round3.py and the tests use `worst()`.
"""
import itertools
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import scenarios_v3 as G  # noqa: E402
import sim  # noqa: E402
import witness  # noqa: E402

TOP = G.FLOORS - 1


def _pattern(name, i):
    """(origin, destination) for caller i."""
    table = {
        "shuttle": (0, TOP),                                  # the audit's probe: full up, empty back
        "scatter": (0, 1 + (TOP - 1 - i % 29 + 29) % 29),     # every stop different on the way up
        "pickups": (i % 10, 20 + i % 10),                     # stops to collect and stops to drop
        "top_down": (TOP, 0),
        "two_ends": ((0, TOP) if i % 2 else (TOP, 0)),
        "all_floors": (i % 29, TOP),
        "short_hops": (i % 29, i % 29 + 1),
    }
    return table[name]


def _earliest(family, cost):
    """Each caller as early as the envelope allows, given the floors the pattern gives them."""
    env, placed, tick = G.ENVELOPE[family], [], 0
    for i in range(env["calls"]):
        origin, dest = cost(i)
        while True:
            trial = placed + [("call", tick, origin, dest)]
            if not G._check_traffic_partial(family, trial):
                placed = trial
                break
            tick += 1
    return placed


PATTERNS = ("shuttle", "scatter", "pickups", "top_down", "two_ends", "all_floors", "short_hops")


def _rush_calls(upper_pattern, lobby_pattern):
    placed, tick = [], 0
    env = G.ENVELOPE["v5"]
    order = [("upper", i) for i in range(env["upper"])] + [("lobby", i) for i in range(env["lobby"])]
    for kind, i in order:
        if kind == "upper":
            origin, dest = {"top_down": (TOP, 1), "shuttle": (1, TOP), "all_floors": (1 + i % 29, 0 if i % 2 else TOP - (i % 28)),
                            "scatter": (1 + i % 29, 1 + (i + 14) % 29)}[upper_pattern]
            if origin == dest:
                dest = 1 if origin != 1 else 2
        else:
            origin, dest = 0, {"shuttle": TOP, "scatter": 1 + i % 29}[lobby_pattern]
        while True:
            trial = placed + [("call", tick, origin, dest)]
            if not G._check_traffic_partial("v5", trial):
                placed = trial
                break
            tick += 1
        tick = tick if kind == "upper" or i else 0
    return placed


def _outage_sets():
    """Permitted maintenance: one lift out for good and a second out for the full two minutes, at several moments."""
    sets = [[("service", 0, 0, False)]]
    for a in (0, 30, 60, 120, 180, 240):
        sets.append([("service", 0, 0, False), ("service", a, 1, False), ("service", a + 120, 1, True)])
    return sets


def _fire_sets(outages):
    fires = []
    for start in (60, 120, 180):
        fires.append(outages + [("mode", start, "fire"), ("mode", start + 120, "normal")])
    return fires


def days(family):
    """Every hand-built day for a family, each validated against the envelope."""
    starts = {1: ([TOP], [0]), 3: ([TOP] * 3, [0] * 3, [TOP, 15, 0])}[G.LIFTS[family]]
    out = []
    if family == "v5":
        for up, low, start in itertools.product(("top_down", "shuttle", "all_floors", "scatter"), ("shuttle", "scatter"), starts):
            out.append((f"v5:{up}+{low}", _rush_calls(up, low), start))
    else:
        for name, start in itertools.product(PATTERNS, starts):
            calls = _earliest(family, lambda i, n=name: _pattern(n, i))
            extras = [[]]
            if family == "v3":
                extras = _outage_sets()
            elif family == "v4":
                extras = [f for o in _outage_sets() for f in _fire_sets(o)]
            for k, extra in enumerate(extras):
                out.append((f"{family}:{name}:{k}", calls + extra, start))
    return out


def run_day(policy, family, name, events, start):
    problems = G.validate_schedule(family, events)
    if problems:
        raise ValueError(f"{name} is outside the envelope: {problems}")
    sc = {"name": name, "floors": G.FLOORS, "lifts": G.LIFTS[family], "start_floors": list(start),
          "events": sorted(events, key=lambda e: e[1]), "max_ticks": G.MAX_TICKS, "bound": None}
    return sim.Simulation(policy, sc).run()


def worst(family, policy=witness.Sweep):
    """The worst each measure reaches on this family's hand-built days, with where and how many days were tried."""
    best = {"everyone": (0, None), "lobby_p95": (0, None), "upper": (0, None), "safety": 0, "undelivered": 0, "days": 0}
    for name, events, start in days(family):
        r = run_day(policy, family, name, events, start)
        best["days"] += 1
        best["safety"] += sum(r["violations"][k] for k in ("C1", "S1", "S2", "S3"))
        best["undelivered"] += r["violations"]["L1"]
        for key, value in (("everyone", r["max_time"]), ("lobby_p95", r["lobby_p95"]), ("upper", r["rush_upper_max"])):
            if value is not None and value > best[key][0] and (family == "v5" or key == "everyone"):
                best[key] = (value, name)
    return best


if __name__ == "__main__":
    for fam in ("v1", "v2", "v3", "v4", "v5"):
        print(fam, worst(fam), flush=True)
