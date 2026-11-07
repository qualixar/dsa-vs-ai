# Lift control service: product brief

You are building the control software for the lift of a 30-floor building (floors 0 to 29), in
Python, using the standard library only. Nothing else is installed. Version control is handled for
you, so don't run `git commit`.

Requirements on this project arrive as change requests, one at a time, as files named CHANGE-v2.md,
CHANGE-v3.md and so on. You will not know a change before it arrives. Every earlier version must keep
working after a change.

The building opens after 150 working minutes. A working minute is measured time while one of the team's
sessions is running; time spent paused on a usage limit doesn't count. The Lead is told the working
minutes left at each planning step. A session still running when the time is up finishes, and what is
in the repository then is what ships.

There is nobody to ask. Where a request is ambiguous or silent, choose the reading most consistent
with the rest of the brief and the change requests so far, write it in STATUS.md under `Assumptions`,
and carry on.

## The interface (fixed; the building calls exactly this)

`dispatcher/__init__.py` must export a class:

    class Dispatcher:
        def __init__(self, floors: int, lifts: int): ...
        def on_call(self, t: int, floor: int, direction: str) -> None: ...     # hall button, "up" or "down"
        def on_car_request(self, t: int, lift: int, floor: int) -> None: ...   # button inside a lift
        def step(self, t: int, floors_now: list[int]) -> list[str]: ...        # one command per lift

Later change requests may add methods to this class.

## How the building behaves

Time runs in ticks of one second. On each tick the building first delivers that tick's events, then
calls `step` with each lift's current floor, then applies your commands.

- `step` returns one command per lift, every tick: "up", "down", "stay" or "open". Moving takes one
  tick per floor. Arriving doesn't open the doors; opening is its own command and takes one tick.
- On "open", riders whose floor this is get off, then people waiting on this floor get on, up to
  10 people per lift, whichever way they are going. Each person who boards presses their floor,
  which reaches you as `on_car_request`.
- If people are still waiting after the lift fills up, they press the hall button again, and you get
  a new `on_call` for that floor.
- A hall call tells you the floor and direction, not the destination.
- A passenger's time runs from their first call to the tick the doors open at their destination.
  Some runs start with riders already aboard: you get an `on_car_request` for each at t=0, and
  their time starts there.

## Rules the system must always keep

1. `step` returns exactly one valid command per lift on every tick, and no method raises.
2. A lift is never commanded past floor 0 or the top floor.
3. Every passenger reaches their destination within the time limit for the version, on days inside
   that version's stated traffic envelope.

Rules 1 and 2 hold on any day. A time limit is promised only on days inside the envelope. Acceptance is
measured on days drawn at random from inside the envelope, not on hand-built worst cases. Nobody claims
that every day you could write down inside an envelope can meet its limit.

## Version 1

One lift. Serve hall and car calls. Keep passengers' time as low as you can.

Traffic envelope: exactly 40 calls in the first 10 minutes of a run, from any floor to any other floor,
mostly at random times. Some days a crowd arrives at one floor on one tick; those people are among the
40. The largest crowd is 12 people. The fastest arrivals allowed are 15 calls in any 10 seconds, 20 in
any 60 seconds and 35 in any 5 minutes.

Time limit: 270 s from first call to arrival, for every passenger, on days inside this envelope.

## How the team is organised

| Role | Owns |
|---|---|
| Lead | PLAN.md, STATUS.md |
| Implementer A | dispatcher/ |
| Implementer B | modes/ (operating modes, imported by dispatcher/; nothing to do until a change needs it) |
| Reviewer | tests/, REVIEW.md |

Tests run with `python3 -m unittest discover -s tests` from the project root. A version counts as
finished when the Lead writes `DONE vN` as the first line of STATUS.md.
