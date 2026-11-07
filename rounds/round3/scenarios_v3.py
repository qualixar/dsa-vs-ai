"""Round three days. Every day is built from (family, seed), and a finished day must obey the envelope the
brief states; a draw that breaks it, including after the fire edits, is thrown away and drawn again.

The real seed list comes from a hash of the frozen inputs plus a random salt drawn after that hash is recorded
(see tools/round3_seal.py). Teams never see this file, the seeds or any result.
"""
import hashlib
import json
import os
import random

import scenarios  # noqa: E402  (the riders-aboard batches are unchanged)

FLOORS = 30
LIFTS = {"v1": 1, "v2": 3, "v3": 3, "v4": 3, "v5": 3}
MAX_TICKS = 6000

# The arrival envelope, word for word what BRIEF.md and the change requests state.
# crowd = most calls from one floor on one tick; windows = (seconds, most calls in any such window).
ENVELOPE = {
    "v1": {"calls": 40, "until": 600, "crowd": 12, "windows": ((10, 15), (60, 20), (300, 35))},
    "v2": {"calls": 120, "until": 600, "crowd": 15, "windows": ((10, 35), (60, 50), (300, 90))},
    "v5": {"calls": 300, "until": 300, "crowd": 6, "windows": ((10, 25), (60, 85)),
           "lobby": 240, "upper": 60, "upper_windows": ((60, 25),)},
}
ENVELOPE["v3"] = ENVELOPE["v4"] = ENVELOPE["v2"]
TWO_OUT_MAX_S = 120
LIFTS_OUT_MAX = 2
FIRE_START = (60, 480)    # the fire starts in this half-open range of ticks
FIRE_LENGTH = (10, 120)   # seconds, inclusive

# Checked by calibrate_round3.py --check, one procedure for all.
LIMITS = {"v1": 270, "v2": 290, "v3": 510, "v4": 590, "v5": 1850}
LOBBY_P95_LIMIT = 1760    # v5: 95th percentile of riders who board at the lobby
RUSH_UPPER_LIMIT = 190    # v5: every rider who boards above the lobby

CERTIFICATE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "sealed", "REFEREE-CERTIFICATE.json")


def _destination(rng, origin):
    d = rng.randrange(FLOORS - 1)
    return d + 1 if d >= origin else d


def _calls(rng, n, until, origins=None):
    out = []
    for _ in range(n):
        origin = rng.randrange(FLOORS) if origins is None else rng.choice(origins)
        out.append(("call", rng.randrange(until), origin, _destination(rng, origin)))
    return out


def _crowd(rng, n):
    t, floor = rng.randrange(0, 500), rng.randrange(FLOORS)
    return [("call", t, floor, _destination(rng, floor)) for _ in range(n)]


def _burst(rng, n):
    t0 = rng.randrange(0, 500)
    return [("call", t0 + rng.randrange(10), o, d) for _, _, o, d in _calls(rng, n, 10)]


def _traffic(rng, family):
    total = ENVELOPE[family]["calls"]
    if family == "v5":
        return (_calls(rng, ENVELOPE["v5"]["lobby"], 300, origins=[0])
                + _calls(rng, ENVELOPE["v5"]["upper"], 300, origins=list(range(1, FLOORS))))
    crowd = ENVELOPE[family]["crowd"]
    r = rng.random()
    if family == "v1":
        return _calls(rng, total - crowd, 600) + _crowd(rng, crowd) if r < 0.25 else _calls(rng, total, 600)
    if r < 0.25:
        return _calls(rng, total - crowd, 600) + _crowd(rng, crowd)
    if r < 0.5:
        return _calls(rng, total - 30, 600) + _burst(rng, 30)
    return _calls(rng, total, 600)


def _outages(rng):
    lifts = [0, 1, 2]
    rng.shuffle(lifts)
    pattern = rng.choice(["rest_of_run", "window", "two_overlap", "from_start", "window", "two_overlap"])
    if pattern == "rest_of_run":
        return [("service", rng.randrange(0, 500), lifts[0], False)]
    if pattern == "from_start":
        return [("service", 0, lifts[0], False), ("service", rng.randrange(60, 300), lifts[0], True)]
    if pattern == "window":
        a = rng.randrange(0, 500)
        return [("service", a, lifts[0], False), ("service", a + rng.randrange(5, 200), lifts[0], True)]
    a, overlap = rng.randrange(0, 450), rng.randrange(5, TWO_OUT_MAX_S + 1)
    b = a + rng.randrange(0, 60)
    events = [("service", a, lifts[0], False), ("service", b + overlap, lifts[0], True), ("service", b, lifts[1], False)]
    if rng.random() < 0.5:
        events.append(("service", b + overlap + rng.randrange(0, 150), lifts[1], True))
    return events


def _with_fire(rng, outages):
    """One fire. On about two days in five a lift is out when it starts and comes back during it, which moves that
    lift's return, so the caller validates the finished schedule rather than trusting this edit."""
    start, length = rng.randrange(*FIRE_START), rng.randrange(FIRE_LENGTH[0], FIRE_LENGTH[1] + 1)
    down = [e for e in outages if not e[3] and e[1] <= 450]
    events = list(outages)
    if down and rng.random() < 0.45:
        chosen = rng.choice(down)
        start = max(FIRE_START[0], chosen[1] + rng.randrange(1, 30))
        events = [e for e in events if not (e[2] == chosen[2] and e[3])]
        events.append(("service", start + rng.randrange(2, max(3, length - 1)), chosen[2], True))
    return events + [("mode", start, "fire"), ("mode", start + length, "normal")]


def busiest(times, window):
    """Most calls in any window of `window` seconds."""
    ordered, best, first = sorted(times), 0, 0
    for i, t in enumerate(ordered):
        while ordered[first] <= t - window:
            first += 1
        best = max(best, i - first + 1)
    return best


def _check_traffic(family, calls):
    env, bad = ENVELOPE[family], []
    if len(calls) != env["calls"]:
        bad.append(f"{len(calls)} calls, the envelope says {env['calls']}")
    if any(not 0 <= e[1] < env["until"] for e in calls):
        bad.append(f"a call outside the first {env['until']} s")
    if any(e[2] == e[3] or not (0 <= e[2] < FLOORS and 0 <= e[3] < FLOORS) for e in calls):
        bad.append("a call to the same floor or off the building")
    tally = {}
    for e in calls:
        tally[(e[1], e[2])] = tally.get((e[1], e[2]), 0) + 1
    if tally and max(tally.values()) > env["crowd"]:
        bad.append(f"a crowd of {max(tally.values())}, largest allowed {env['crowd']}")
    for window, most in env["windows"]:
        seen = busiest([e[1] for e in calls], window)
        if seen > most:
            bad.append(f"{seen} calls in {window} s, most allowed {most}")
    if "lobby" in env:
        lobby = [e for e in calls if e[2] == 0]
        if len(lobby) != env["lobby"] or any(e[3] == 0 for e in lobby):
            bad.append(f"{len(lobby)} lobby calls, the envelope says {env['lobby']}")
        upper = [e[1] for e in calls if e[2] != 0]
        for window, most in env["upper_windows"]:
            if busiest(upper, window) > most:
                bad.append(f"{busiest(upper, window)} upstairs calls in {window} s, most allowed {most}")
    return bad


def _check_traffic_partial(family, calls):
    """The caps alone, for hand-built days still being placed: totals are checked when the day is finished."""
    env, bad = ENVELOPE[family], []
    tally = {}
    for e in calls:
        tally[(e[1], e[2])] = tally.get((e[1], e[2]), 0) + 1
    if tally and max(tally.values()) > env["crowd"]:
        bad.append("crowd")
    for window, most in env["windows"]:
        if busiest([e[1] for e in calls], window) > most:
            bad.append("window")
    for window, most in env.get("upper_windows", ()):
        if busiest([e[1] for e in calls if e[2] != 0], window) > most:
            bad.append("upper window")
    return bad


def _check_service(family, service):
    if family in ("v1", "v2", "v5"):
        return ["a lift taken out in a version without maintenance"] if service else []
    bad, out, two_out, last = [], set(), 0, 0
    taken = {}
    for e in sorted(service, key=lambda e: (e[1], e[3])):
        if len(out) >= 2:
            two_out += e[1] - last
        last = e[1]
        if e[3]:
            out.discard(e[2])
        else:
            out.add(e[2])
            taken[e[2]] = taken.get(e[2], 0) + 1
        if len(out) >= LIFTS[family]:
            bad.append("every lift out at once")
    if len(out) >= 2:
        bad.append("two lifts out with no return")
    if two_out > TWO_OUT_MAX_S:
        bad.append(f"two lifts out for {two_out} s in total")
    if len(taken) > LIFTS_OUT_MAX:
        bad.append("more than two lifts taken out in a run")
    if any(n > 1 for n in taken.values()):
        bad.append("a lift taken out twice in a run")
    return bad


def _check_fire(family, modes):
    if family != "v4":
        return ["a fire in a version without fire mode"] if modes else []
    if len(modes) != 2 or modes[0][2] != "fire" or modes[1][2] != "normal":
        return ["v4 has exactly one fire"]
    start, length = modes[0][1], modes[1][1] - modes[0][1]
    bad = []
    if not FIRE_START[0] <= start < FIRE_START[1]:
        bad.append(f"fire starts at {start}")
    if not FIRE_LENGTH[0] <= length <= FIRE_LENGTH[1]:
        bad.append(f"fire lasts {length} s")
    return bad


def validate_schedule(family, events):
    """Every way a finished day breaks the stated envelope. An empty list means it's inside."""
    ordered = sorted(events, key=lambda e: e[1])
    return (_check_traffic(family, [e for e in ordered if e[0] == "call"])
            + _check_service(family, [e for e in ordered if e[0] == "service"])
            + _check_fire(family, [e for e in ordered if e[0] == "mode"]))


def _draw(family, seed, attempt):
    rng = random.Random(f"{family}:{seed}:{attempt}")
    events = _traffic(rng, family)
    if family in ("v3", "v4"):
        outages = _outages(rng)
        events += _with_fire(rng, outages) if family == "v4" else outages
    return rng, sorted(events, key=lambda e: e[1])


def scenario(family, seed, limits=None):
    """One day. A deterministic function of (family, seed): a draw outside the envelope moves to the next attempt."""
    for attempt in range(1000):
        rng, events = _draw(family, seed, attempt)
        if not validate_schedule(family, events):
            return _day(family, seed, attempt, rng, events, limits or current_limits())
    raise RuntimeError(f"no valid day for {family}:{seed} in 1000 draws")


def _day(family, seed, attempt, rng, events, limits):
    n = LIFTS[family]
    return {"name": f"{family}-{seed}", "floors": FLOORS, "lifts": n,
            "start_floors": [rng.randrange(FLOORS) for _ in range(n)], "events": events, "max_ticks": MAX_TICKS,
            "bound": limits["everyone"][family], "attempt": attempt,
            "lobby_p95_target": limits["lobby_p95"] if family == "v5" else None,
            "rush_upper_limit": limits["upper"] if family == "v5" else None}


def current_limits():
    return {"everyone": dict(LIMITS), "lobby_p95": LOBBY_P95_LIMIT, "upper": RUSH_UPPER_LIMIT}


def seeds(family, sealed_hash, salt, count):
    """Seeds from the frozen inputs' hash and the salt drawn after it. Neither alone gives a day."""
    out, i = [], 0
    while len(out) < count:
        value = int(hashlib.sha256(f"{sealed_hash}:{salt}:{family}:{i}".encode()).hexdigest()[:12], 16)
        if value not in out:
            out.append(value)
        i += 1
    return out


def certified_set(path=CERTIFICATE):
    """{family: [day, ...]} from the certificate, in its order, plus the riders-aboard batches."""
    with open(path) as f:
        certificate = json.load(f)
    days = {fam: [scenario(fam, seed) for seed in entry["kept_seeds"]] for fam, entry in certificate["families"].items()}
    return days, scenarios.q1_batches()


q1_batches = scenarios.q1_batches
