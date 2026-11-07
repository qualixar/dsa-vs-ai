"""Building simulator for Act 3. Replays a fixed event script against a
Dispatcher (the contract in BRIEF.md) and records every rule it breaks.

Time runs in ticks of one second. Each tick:
  1. events due this tick are delivered (calls, lift out of / back in service, fire mode);
  2. step(t, floors_now) gets each lift's current floor (its sensors) and returns
     one command per lift: "up", "down", "stay" or "open";
  3. commands are applied. "open" lets passengers off (destination reached) and,
     in normal mode, lets waiting passengers on (capacity 10); each boarding
     passenger presses their floor, which the dispatcher receives as on_car_request.

Rules checked:
  C1 contract   step() returns exactly one valid command per lift and doesn't raise
  S1 bounds     a lift never moves below floor 0 or above the top floor
  S2 fire       in fire mode: no lift moves up, no doors open except at floor 0, and from
                tick (fire start + floors + 2) every lift in service is at floor 0 and commanded
                "open" (a lift returning to service during fire gets the same time from its return)
  S3 service    a lift out of service never moves or opens
  L1 liveness   every passenger arrives within the version's bound
  T5 rush goal  (v5) 95th-percentile trip time within the stated target
  T5b lobby     (round three, v5) 95th percentile of riders who board at the lobby, when the day sets a target
  T5c upstairs  (round three, v5) every rider who boards above the lobby, when the day sets a limit

Every passenger finishes for one recorded reason, each checked against its legal transition: normal arrival (doors
open at their floor), maintenance arrival (the building lets them out at their floor when the lift is withdrawn) or
evacuation (doors open at floor 0 in fire mode). A conservation check runs on every tick. A breach of either is a
fault in this simulator, raises SimulatorError and voids the run: it can never score against a team.
"""
import math

COMMANDS = {"up", "down", "stay", "open"}
CAPACITY = 10
REASONS = ("normal", "maintenance", "evacuated")


class SimulatorError(BaseException):
    """Our simulator broke its own books. Outside Exception on purpose, so nothing records it as a team's failure."""


class Passenger:
    __slots__ = ("pid", "origin", "origin0", "dest", "t_call", "t_done", "lift", "evacuated", "reason")

    def __init__(self, pid, origin, dest, t_call):
        self.pid, self.origin, self.origin0, self.dest, self.t_call = pid, origin, origin, dest, t_call
        self.t_done, self.lift, self.evacuated, self.reason = None, None, False, None


class Lift:
    __slots__ = ("floor", "available", "riders", "back_at")

    def __init__(self, floor):
        self.floor, self.available, self.riders, self.back_at = floor, True, [], None


class Simulation:
    def __init__(self, dispatcher_cls, scenario):
        self.sc = scenario
        self.floors, self.n = scenario["floors"], scenario["lifts"]
        self.lifts = [Lift(scenario.get("start_floors", [0] * self.n)[i]) for i in range(self.n)]
        self.waiting = {}  # floor -> list of passengers
        self.people = []
        self.mode, self.fire_since = "normal", None
        self.violations = {"C1": [], "S1": [], "S2": [], "S3": []}
        self.commands_log = []
        try:
            self.d = dispatcher_cls(self.floors, self.n)
        except Exception as e:
            self.d = None
            self.violations["C1"].append((0, f"constructor raised {type(e).__name__}: {e}"))

    # ---- helpers -------------------------------------------------------
    def _flag(self, rule, t, msg):
        if len(self.violations[rule]) < 50:
            self.violations[rule].append((t, msg))

    def _call(self, fn, *args):
        try:
            return getattr(self.d, fn)(*args), None
        except Exception as e:
            return None, f"{fn} raised {type(e).__name__}: {e}"

    def _finish(self, p, t, reason, lift):
        """The only way anyone finishes. Each reason has one legal transition; anything else is our bug."""
        legal = {"normal": lift.floor == p.dest and lift.available and self.mode != "fire",
                 "maintenance": lift.floor == p.dest and not lift.available,
                 "evacuated": lift.floor == 0 and lift.available and self.mode == "fire"}
        if not legal.get(reason, False):
            raise SimulatorError(f"t={t}: passenger {p.pid} finished as {reason!r} at floor {lift.floor}")
        p.t_done, p.reason, p.lift, p.evacuated = t, reason, None, reason == "evacuated"

    def _conserve(self, t):
        """Each passenger is in exactly one place: waiting, riding or finished."""
        places = [p.pid for ps in self.waiting.values() for p in ps]
        places += [p.pid for lift in self.lifts for p in lift.riders]
        places += [p.pid for p in self.people if p.t_done is not None]
        if len(places) != len(self.people) or len(set(places)) != len(self.people):
            raise SimulatorError(f"t={t}: {len(places)} places for {len(self.people)} passengers")

    def _hall_call(self, t, p):
        self.waiting.setdefault(p.origin, []).append(p)
        _, err = self._call("on_call", t, p.origin, "up" if p.dest > p.origin else "down")
        if err:
            self._flag("C1", t, err)

    # ---- events --------------------------------------------------------
    def _deliver_events(self, t, events):
        for ev in events:
            kind = ev[0]
            if kind == "call":
                p = Passenger(len(self.people), ev[2], ev[3], t)
                self.people.append(p)
                self._hall_call(t, p)
            elif kind == "onboard":  # passenger already inside a lift at t=0 (Q1 batches)
                p = Passenger(len(self.people), self.lifts[ev[2]].floor, ev[3], t)
                p.lift = ev[2]
                self.people.append(p)
                self.lifts[ev[2]].riders.append(p)
                _, err = self._call("on_car_request", t, ev[2], ev[3])
                if err:
                    self._flag("C1", t, err)
            elif kind == "service":
                lift, ok = self.lifts[ev[2]], ev[3]
                lift.available = ok
                lift.back_at = t if ok else None
                _, err = self._call("set_lift_available", t, ev[2], ok)
                if err:
                    self._flag("C1", t, err)
                if not ok:  # the building lets riders out here; they call again
                    riders, lift.riders = lift.riders, []
                    for p in riders:
                        p.lift = None
                        if p.dest == lift.floor:
                            self._finish(p, t, "maintenance", lift)
                        else:
                            p.origin = lift.floor
                            self._hall_call(t, p)
            elif kind == "mode":
                self.mode = ev[2]
                self.fire_since = t if ev[2] == "fire" else None
                _, err = self._call("set_mode", t, ev[2])
                if err:
                    self._flag("C1", t, err)
                if ev[2] == "normal":  # pending hall calls are sent again
                    for floor, ps in sorted(self.waiting.items()):
                        for p in ps:
                            _, err = self._call("on_call", t, floor, "up" if p.dest > floor else "down")
                            if err:
                                self._flag("C1", t, err)

    # ---- one tick ------------------------------------------------------
    def _commands(self, t):
        cmds, err = self._call("step", t, [l.floor for l in self.lifts])
        if err:
            self._flag("C1", t, err)
            return ["stay"] * self.n
        if not isinstance(cmds, list) or len(cmds) != self.n:
            self._flag("C1", t, f"step returned {str(cmds)[:60]} (need {self.n} commands)")
            return ["stay"] * self.n
        out = []
        for i, c in enumerate(cmds):
            if not isinstance(c, str) or c not in COMMANDS:
                self._flag("C1", t, f"lift {i}: invalid command {str(c)[:20]}")
                c = "stay"
            out.append(c)
        return out

    def _open(self, t, i, lift):
        if self.mode == "fire":
            if lift.floor != 0:
                self._flag("S2", t, f"lift {i} opened at floor {lift.floor} in fire mode")
                return
            for p in lift.riders:
                self._finish(p, t, "evacuated", lift)
            lift.riders = []
            return
        staying = []
        for p in lift.riders:
            if p.dest == lift.floor:
                self._finish(p, t, "normal", lift)
            else:
                staying.append(p)
        lift.riders = staying
        queue = self.waiting.get(lift.floor, [])
        while queue and len(lift.riders) < CAPACITY:
            p = queue.pop(0)
            p.lift = i
            lift.riders.append(p)
            _, err = self._call("on_car_request", t, i, p.dest)
            if err:
                self._flag("C1", t, err)
        for d in sorted({"up" if p.dest > lift.floor else "down" for p in queue}):
            _, err = self._call("on_call", t, lift.floor, d)  # left behind: they press again
            if err:
                self._flag("C1", t, err)

    def _apply(self, t, cmds):
        for i, (lift, c) in enumerate(zip(self.lifts, cmds)):
            if not lift.available:
                if c != "stay":
                    self._flag("S3", t, f"lift {i} out of service but commanded {c}")
                continue
            if c in ("up", "down"):
                if self.mode == "fire" and c == "up":
                    self._flag("S2", t, f"lift {i} moved up in fire mode")
                nxt = lift.floor + (1 if c == "up" else -1)
                if not 0 <= nxt < self.floors:
                    self._flag("S1", t, f"lift {i} commanded past the shaft (floor {nxt})")
                    continue
                lift.floor = nxt
            elif c == "open":
                self._open(t, i, lift)
        if self.mode == "fire":
            for i, (lift, c) in enumerate(zip(self.lifts, cmds)):
                start = max(self.fire_since, lift.back_at or 0)
                if t >= start + self.floors + 2 and lift.available and (lift.floor != 0 or c != "open"):
                    self._flag("S2", t, f"lift {i} not parked open at floor 0 during fire mode")

    # ---- run -----------------------------------------------------------
    def run(self):
        events = {}
        for ev in self.sc["events"]:
            events.setdefault(ev[1], []).append(ev)
        horizon = self.sc["max_ticks"]
        if self.d is not None:
            for t in range(horizon):
                self._deliver_events(t, events.get(t, []))
                cmds = self._commands(t)
                self.commands_log.append(cmds)
                self._apply(t, cmds)
                self._conserve(t)
                fire_open = self.mode == "fire" and t <= self.fire_since + self.floors + 2
                if t >= max(events, default=0) and not fire_open and all(p.t_done is not None for p in self.people):
                    break
        return self.report()

    def report(self):
        served = [p for p in self.people if p.t_done is not None and not p.evacuated]
        times = sorted(p.t_done - p.t_call for p in served)
        bound = self.sc.get("bound")
        late = [p.pid for p in self.people if not p.evacuated and
                (p.t_done is None or (bound is not None and p.t_done - p.t_call > bound))]
        p95 = times[min(len(times) - 1, math.ceil(0.95 * len(times)) - 1)] if times else None
        target = self.sc.get("p95_target")
        missed = 1 if target is not None and (p95 is None or p95 > target) else 0
        extra = self._rush_report(served)
        return {
            "scenario": self.sc["name"],
            "violations": {k: len(v) for k, v in self.violations.items()} | {"L1": len(late), "T5": missed} | extra.pop("violations"),
            "examples": {k: v[:3] for k, v in self.violations.items() if v} |
                        ({"L1": late[:5]} if late else {}),
            "max_time": times[-1] if times else None,
            "completions": {r: sum(p.reason == r for p in self.people) for r in REASONS},
            **extra,
            "passengers": len(self.people), "delivered": len(served),
            "total_time": sum(times), "mean_time": round(sum(times) / len(times), 2) if times else None,
            "p95_time": p95,
        }

    def _rush_report(self, served):
        """Riders are split by the floor they first called from: a rider's origin moves if a lift is withdrawn."""
        lobby = sorted(p.t_done - p.t_call for p in served if p.origin0 == 0)
        upper = [p.t_done - p.t_call for p in served if p.origin0 != 0]
        out = {"lobby_p95": lobby[math.ceil(0.95 * len(lobby)) - 1] if lobby else None,
               "rush_upper_max": max(upper) if upper else None, "violations": {}}
        target, limit = self.sc.get("lobby_p95_target"), self.sc.get("rush_upper_limit")
        if target is not None:
            out["violations"]["T5b"] = 1 if out["lobby_p95"] is None or out["lobby_p95"] > target else 0
        if limit is not None:
            stranded = any(p.origin0 != 0 and p.t_done is None for p in self.people)
            out["violations"]["T5c"] = 1 if stranded or any(t > limit for t in upper) else 0
        return out


def optimum_onboard(start, dests):
    """Exact best total for one lift with riders already aboard (Q1): try every
    order of stops; travel takes the distance, each stop costs one tick to open.
    A rider is done on the tick the doors open at their floor."""
    import itertools
    best = None
    for order in itertools.permutations(dests):
        t, pos, total = 0, start, 0
        for f in order:
            t += abs(pos - f)
            total += t
            t += 1
            pos = f
        best = total if best is None else min(best, total)
    return best or 0
