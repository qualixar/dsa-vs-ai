"""Reference dispatchers. `Baseline` is the published comparison point for Q2
(nearest-car assignment with sweeping), and calibrates the liveness bounds.
The others are deliberately broken, so the self-tests can prove each check fires."""
import itertools


class Baseline:
    def __init__(self, floors, lifts):
        self.floors, self.n = floors, lifts
        self.hall = {}                       # floor -> assigned lift
        self.car = [set() for _ in range(lifts)]
        self.dir = ["idle"] * lifts
        self.up = [True] * lifts
        self.pos = [0] * lifts
        self.fire = False
        self.opened_at = [None] * lifts      # floor of the last open, until the lift moves

    def on_call(self, t, floor, direction):
        if floor not in self.hall:
            self.hall[floor] = self._nearest(floor)

    def on_car_request(self, t, lift, floor):
        self.car[lift].add(floor)

    def set_mode(self, t, mode):
        self.fire = mode == "fire"
        if not self.fire:
            self.hall.clear()                # the building sends pending calls again

    def set_lift_available(self, t, lift, available):
        self.up[lift] = available
        self.opened_at[lift] = None
        if not available:
            self.car[lift].clear()           # riders are let out and call again
            for f, l in list(self.hall.items()):
                if l == lift:
                    self.hall[f] = self._nearest(f)

    def _nearest(self, floor):
        live = [i for i in range(self.n) if self.up[i]] or list(range(self.n))
        return min(live, key=lambda i: (abs(self.pos[i] - floor), i))

    def _targets(self, i):
        return self.car[i] | {f for f, l in self.hall.items() if l == i}

    def step(self, t, floors_now):
        self.pos = list(floors_now)
        return [self._command(i) for i in range(self.n)]

    def _command(self, i):
        if not self.up[i]:
            return "stay"
        here = self.pos[i]
        if self.fire:
            return "down" if here > 0 else "open"
        targets = self._targets(i)
        if here in targets and (self.opened_at[i] != here or here in self.car[i]):
            self.car[i].discard(here)
            self.hall.pop(here, None)
            self.opened_at[i] = here
            return "open"
        if self.opened_at[i] == here:          # just opened here (likely full): move on first
            targets = targets - {here}
        if not targets:
            self.dir[i] = "idle"
            self.opened_at[i] = None           # idle here: a new call at this floor must reopen
            return "stay"
        above = any(f > here for f in targets)
        below = any(f < here for f in targets)
        if self.dir[i] == "up" and above or (self.dir[i] != "down" and above and not below):
            self.dir[i] = "up"
        elif below:
            self.dir[i] = "down"
        else:
            self.dir[i] = "up"
        self.opened_at[i] = None
        return "up" if self.dir[i] == "up" else "down"


class OptimalOnboard(Baseline):
    """For Q1 batches only: follows the exact best stop order. Proves the
    simulator's timing matches the optimum formula (gap must be 0)."""
    def __init__(self, floors, lifts):
        super().__init__(floors, lifts)
        self.plan = None

    def _command(self, i):
        here = self.pos[i]
        if self.plan is None:
            best = None
            for order in itertools.permutations(sorted(self.car[i])):
                tt, p, tot = 0, here, 0
                for f in order:
                    tt += abs(p - f); tot += tt; tt += 1; p = f
                if best is None or tot < best[0]:
                    best = (tot, list(order))
            self.plan = best[1] if best else []
        if not self.plan:
            return "stay"
        if here == self.plan[0]:
            self.plan.pop(0)
            self.car[i].discard(here)
            return "open"
        return "up" if self.plan[0] > here else "down"


class IgnoresFire(Baseline):
    def set_mode(self, t, mode):
        pass


class MovesWhileOutOfService(Baseline):
    def _command(self, i):
        return "up" if not self.up[i] else super()._command(i)


class WrongCommandCount(Baseline):
    def step(self, t, floors_now):
        return super().step(t, floors_now)[:-1] if t > 50 else super().step(t, floors_now)


class FallsThroughFloor(Baseline):
    def _command(self, i):
        c = super()._command(i)
        return "down" if c == "stay" and self.pos[i] == 0 else c


class OnlyCarCalls(Baseline):
    """Never answers hall buttons: people waiting outside are never picked up."""
    def on_call(self, t, floor, direction):
        pass
