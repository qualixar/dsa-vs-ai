"""Pure, sweep-aware assignment of shared hall floors to lift cars.

``positions`` and ``directions`` are the latest per-car snapshots (direction
is -1, 0, or +1); ``car_counts[i]`` maps destination floors to outstanding
passenger counts. ``owners`` is the previous floor-to-car assignment, used to
keep service stable. ETA estimates travel to an opening along each car's
current sweep, including reversal after ahead work and one tick at intervening
stops. This is necessarily an approximation: future calls and boarding are
unknown. Floors are considered in sorted order, ties go to the lower car
index, and prior ownership is retained unless another eligible car is at
least three estimated ticks sooner. Full cars (10 or more passengers) are
ineligible; if all cars are full, those hall floors remain unassigned for the
dispatcher to retain and retry on a later snapshot.
"""


class LiftAvailability:
    """Track whether each configured lift is in service.

    All lifts start available. ``set_available`` returns True only when a
    valid setting changes a lift's state; invalid indices or non-bool values
    return False without changing state. ``snapshot`` returns an immutable,
    car-index-aligned tuple, so changing a caller's copy cannot affect this
    object.
    """

    def __init__(self, lifts):
        # Dispatcher supplies its normalized, nonnegative lift count.
        self._available = [True] * lifts

    def set_available(self, lift, available):
        """Set a lift's availability; report whether a transition occurred."""
        if type(lift) is not int or not 0 <= lift < len(self._available):
            return False
        if type(available) is not bool:
            return False
        if self._available[lift] == available:
            return False
        self._available[lift] = available
        return True

    def is_available(self, lift):
        """Return a valid lift's state, or False for an invalid index."""
        if type(lift) is not int or not 0 <= lift < len(self._available):
            return False
        return self._available[lift]

    def snapshot(self):
        """Return an immutable tuple of states in lift-index order."""
        return tuple(self._available)


def _passenger_count(counts):
    """Return a safe nonnegative sum for a per-floor passenger mapping."""
    if not hasattr(counts, "values"):
        return 0
    total = 0
    for count in counts.values():
        if type(count) is int and count > 0:
            total += count
    return total


def _eta(lift, floor, positions, directions, car_counts, assigned):
    """Estimate ticks until this car can open at ``floor``."""
    here = positions[lift]
    direction = directions[lift]
    destinations = car_counts[lift]
    stops = set(destinations) | assigned

    # An idle empty car follows the dispatcher's nearest-stop policy.
    if not destinations and not assigned:
        return abs(floor - here) + 1

    if floor in stops:
        return abs(floor - here) + 1

    ahead = [stop for stop in stops
             if direction in (-1, 1) and (stop - here) * direction > 0]
    if not direction or not ahead:
        return abs(floor - here) + 1

    farthest = max(ahead) if direction > 0 else min(ahead)
    distance = abs(farthest - here) + abs(floor - farthest)
    low = min(here, farthest, floor)
    high = max(here, farthest, floor)
    # Include a tick for each known stop passed on the way to/reversing toward
    # the requested floor. A stop shared with the target adds only one opening.
    opening_ticks = sum(1 for stop in stops if low <= stop <= high)
    return distance + opening_ticks + 1


def assign_halls(hall_floors, owners, positions, directions, car_counts,
                 floors):
    """Return one eligible car index for each active shared hall floor.

    Inputs are read-only snapshots. The fresh result contains no inactive
    floors and never assigns a hall floor to a full car.
    """
    try:
        floor_limit = int(floors)
        car_total = min(len(positions), len(directions), len(car_counts))
    except (TypeError, ValueError, OverflowError):
        return {}
    if floor_limit <= 0 or car_total <= 0:
        return {}

    # Ignore malformed snapshot entries rather than allowing them to cause an
    # exception in the callback-facing dispatcher.
    pos = list(positions[:car_total])
    dirs = list(directions[:car_total])
    counts = list(car_counts[:car_total])
    valid_cars = [i for i in range(car_total)
                  if type(pos[i]) is int and 0 <= pos[i] < floor_limit]
    eligible = [i for i in valid_cars if _passenger_count(counts[i]) < 10]
    result = {}
    allocated = {i: set() for i in range(car_total)}

    try:
        active = sorted({f for f in hall_floors
                         if type(f) is int and 0 <= f < floor_limit})
    except TypeError:
        return {}

    for floor in active:
        if not eligible:
            continue
        ranked = [(_eta(i, floor, pos, dirs, counts, allocated[i]), i)
                  for i in eligible]
        best_eta, best = min(ranked)
        old = owners.get(floor) if hasattr(owners, "get") else None
        if old in eligible:
            old_eta = _eta(old, floor, pos, dirs, counts, allocated[old])
            if old_eta - best_eta < 3:
                best = old
        result[floor] = best
        allocated[best].add(floor)
    return result
