"""Seeded event scripts for Act 3. Fixed before any agent run; the same
scripts are replayed against every version from both runs."""
import random

FLOORS = 30
SEEDS = (11, 22, 33)
# Liveness bounds (seconds from call to arrival) = 2x the published baseline's
# worst case over the three seeds, rounded up to 10 (calibrated 4 Nov 2026,
# before any agent run): v1 80 s, v2 88 s, v3 140 s, v4 185 s, v5 1352 s.
BOUNDS = {"v1": 160, "v2": 180, "v3": 280, "v4": 370, "v5": 2710}
# v5 rush-hour goal: 95th-percentile trip time. The baseline's worst seed is 1254 s;
# 3 lifts x 10 people physically cap throughput, so the goal is "no worse than baseline".
P95_TARGET = {"v5": 1260}


def _calls(rng, count, until, origin_bias=None):
    events = []
    for _ in range(count):
        t = rng.randrange(until)
        if origin_bias is not None and rng.random() < 0.8:
            origin, dest = origin_bias, rng.randrange(1, FLOORS)
        else:
            origin = rng.randrange(FLOORS)
            dest = rng.choice([f for f in range(FLOORS) if f != origin])
        events.append(("call", t, origin, dest))
    return sorted(events, key=lambda e: e[1])


def _base(name, lifts, seed, events, max_ticks=6000):
    rng = random.Random(seed * 7)
    return {"name": name, "floors": FLOORS, "lifts": lifts,
            "start_floors": [rng.randrange(FLOORS) for _ in range(lifts)],
            "events": events, "max_ticks": max_ticks, "bound": BOUNDS.get(name.split("-")[0]),
            "p95_target": P95_TARGET.get(name.split("-")[0])}


def version(v, seed):
    rng = random.Random(seed)
    if v == "v1":
        return _base(f"v1-s{seed}", 1, seed, _calls(rng, 40, 600))
    if v == "v2":
        return _base(f"v2-s{seed}", 3, seed, _calls(rng, 120, 600))
    if v == "v3":
        ev = _calls(rng, 120, 600) + [("service", 150, 1, False), ("service", 400, 1, True),
                                      ("service", 300, 2, False)]
        return _base(f"v3-s{seed}", 3, seed, sorted(ev, key=lambda e: e[1]))
    if v == "v4":
        ev = _calls(rng, 120, 600) + [("service", 190, 2, False), ("mode", 200, "fire"), ("service", 225, 2, True),
                                      ("mode", 270, "normal")]
        return _base(f"v4-s{seed}", 3, seed, sorted(ev, key=lambda e: e[1]))
    if v == "v5":
        return _base(f"v5-s{seed}", 3, seed, _calls(rng, 300, 300, origin_bias=0))
    raise ValueError(v)


def all_versions(upto="v5"):
    order = ["v1", "v2", "v3", "v4", "v5"]
    return [version(v, s) for v in order[: order.index(upto) + 1] for s in SEEDS]


def q1_batches(count=20, seed=4242):
    """One lift, riders already aboard with distinct floors: the exact optimum is known."""
    rng = random.Random(seed)
    out = []
    for i in range(count):
        start = rng.randrange(FLOORS)
        dests = rng.sample([f for f in range(FLOORS) if f != start], rng.randint(5, 8))
        out.append({"name": f"q1-{i:02d}", "floors": FLOORS, "lifts": 1, "start_floors": [start],
                    "events": [("onboard", 0, 0, d) for d in dests], "max_ticks": 2000,
                    "bound": None, "q1": {"start": start, "dests": dests}})
    return out
