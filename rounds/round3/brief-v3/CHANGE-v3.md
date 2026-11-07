# Change request v3: maintenance

From the facilities team. A lift can be taken out of service at any moment, even mid-trip, and can
come back later. The interface gains:

    def set_lift_available(self, t: int, lift: int, available: bool) -> None: ...

Rules, which always hold:

- A lift that is out of service gets "stay" on every tick until it returns.
- When a lift goes out of service, the building lets its riders out at that floor and they press
  the hall button again; their clock keeps running. A rider whose destination is that floor has
  arrived. The hall calls that lift was going to answer, and these riders, must be served by the
  other lifts.
- When a lift returns, nothing is re-sent, so keep whatever you need.

Design conditions: at most two lifts are taken out in a run, each at most once; at least one lift
stays in service at all times; two lifts are out together for at most 2 minutes in total across a
run; one lift can stay out for the rest of the run; a lift can be out from the first tick.

Traffic envelope: the same as version 2. Time limit: 510 s for every passenger on days inside this
envelope and these conditions. Versions 1 and 2 must keep working.
