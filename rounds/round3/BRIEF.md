# Elevator control service: product brief

You are building the control software for the lifts of a 30-floor building (floors 0 to 29), in Python, using the standard library only. Nothing else is installed. Version control is handled for you, so don't run `git commit`.

## The interface (fixed; the building calls exactly this)

`dispatcher/__init__.py` must export a class:

```python
class Dispatcher:
    def __init__(self, floors: int, lifts: int): ...
    def on_call(self, t: int, floor: int, direction: str) -> None: ...      # hall button, "up" or "down"
    def on_car_request(self, t: int, lift: int, floor: int) -> None: ...    # button inside a lift
    def set_mode(self, t: int, mode: str) -> None: ...                      # "normal" or "fire"
    def set_lift_available(self, t: int, lift: int, available: bool) -> None: ...
    def step(self, t: int, floors_now: list[int]) -> list[str]: ...         # one command per lift
```

## How the building behaves

Time runs in ticks of one second. On each tick the building first delivers that tick's events, then calls `step` with each lift's current floor, then applies your commands.

- `step` returns one command per lift, every tick: `"up"`, `"down"`, `"stay"` or `"open"`. Moving takes one tick per floor. Arriving doesn't open the doors; opening is its own command and takes one tick.
- On `"open"`, riders whose floor this is get off, then people waiting on this floor get on, up to **10 people per lift**, whichever way they are going. Each person who boards presses their floor, which reaches you as `on_car_request`.
- If people are still waiting after the lift fills up, they press the hall button again, and you get a new `on_call` for that floor.
- A hall call tells you the floor and direction, not the destination.
- A passenger's time runs from their first call to the tick the doors open at their destination. Some runs start with riders already aboard: you get an `on_car_request` for each at t=0, and their time starts there.

## Rules the system must always keep

1. `step` returns exactly one valid command per lift on every tick, and no method raises.
2. A lift is never commanded past floor 0 or the top floor.
3. A lift that is out of service gets `"stay"` on every tick until it returns. When a lift goes out of service, the building lets its riders out at that floor and they press the hall button again; their clock keeps running. A rider whose destination is that floor has arrived. When a lift returns, nothing is re-sent, so keep whatever you need.
4. In fire mode, no lift moves up. Doors open only at floor 0. From tick `fire start + floors + 2` onward, every lift in service must be at floor 0 and be given `"open"` on every tick until the mode returns to normal. A lift that returns to service during fire mode gets the same `floors + 2` ticks, counted from its return.
   - When doors open at floor 0 in fire mode, all riders leave the building, whatever floor they pressed. They are finished: their car requests no longer apply, and they aren't counted in passenger times or limits.
   - Nobody boards during fire mode. Hall calls can still reach you, and people keep waiting.
   - When the mode returns to normal, every waiting person's hall call is sent to you again.
5. Every passenger other than those evacuated in fire mode reaches their destination within the limit for the version (below). The limit counts from their first call.

## Versions (this is the roadmap; you are told when to start each one)

| Version | Change request | Passenger time limit |
|---|---|---|
| v1 | One lift. Serve hall and car calls; minimise total passenger time | 160 s |
| v2 | Three lifts share the hall calls | 180 s |
| v3 | Maintenance: a lift can be taken out of service at any moment, even mid-trip, and can come back later; its passengers and the hall calls assigned to it must be served by the other lifts | 280 s |
| v4 | Fire mode, as in rule 4 | 370 s |
| v5 | Morning rush: up to 300 calls in the first 5 minutes, most of them from floor 0. Keep the 95th-percentile passenger time at or below 1260 s | 2710 s |

The limits apply at the design traffic: 40 calls spread over 10 minutes for v1, 120 calls spread over 10 minutes for v2 to v4, and the rush above for v5. Outside the rush, people call from any floor to any other floor at random.

Every earlier version must keep working. A version counts as finished when the code does what this brief says.

## How the team is organised

| Role | Owns |
|---|---|
| Lead | `PLAN.md`, `STATUS.md` |
| Implementer A | `dispatcher/` |
| Implementer B | `modes/` (maintenance and fire logic, imported by `dispatcher/`) |
| Reviewer | `tests/`, `REVIEW.md` |

Tests run with `python3 -m unittest discover -s tests` from the project root.
