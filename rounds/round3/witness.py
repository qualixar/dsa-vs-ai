"""A plain sweep dispatcher, about 50 lines: the second known solution, used to test hand-built days inside the
envelope (envelope_probes.py). Every lift runs floor 0 to the top and back and stops only to let someone off or to
pick someone up while it has room. It sees exactly what a team sees: hall calls without destinations."""
CAPACITY = 10


class Sweep:
    def __init__(self, floors, lifts):
        self.top, self.n = floors - 1, lifts
        self.hall = set()
        self.car = [{} for _ in range(lifts)]    # lift -> {floor: riders going there}
        self.going_up = [True] * lifts
        self.service = [True] * lifts
        self.fire = False

    def on_call(self, t, floor, direction):
        self.hall.add(floor)

    def on_car_request(self, t, lift, floor):
        self.car[lift][floor] = self.car[lift].get(floor, 0) + 1

    def set_mode(self, t, mode):
        self.fire = mode == "fire"

    def set_lift_available(self, t, lift, available):
        self.service[lift] = available
        if not available:
            self.car[lift] = {}

    def step(self, t, floors_now):
        return [self._command(i, floors_now[i]) for i in range(self.n)]

    def _command(self, i, here):
        if not self.service[i]:
            return "stay"
        if self.fire:
            return self._fire_command(i, here)
        room = sum(self.car[i].values()) < CAPACITY
        if here in self.car[i] or (here in self.hall and room):
            self.car[i].pop(here, None)
            self.hall.discard(here)
            return "open"
        if here == self.top:
            self.going_up[i] = False
        elif here == 0:
            self.going_up[i] = True
        return "up" if self.going_up[i] else "down"

    def _fire_command(self, i, here):
        if here > 0:
            return "down"
        self.car[i] = {}
        self.going_up[i] = True
        return "open"
