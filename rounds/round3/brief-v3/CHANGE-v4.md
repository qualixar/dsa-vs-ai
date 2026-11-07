# Change request v4: fire mode

From the fire safety consultant. The interface gains:

    def set_mode(self, t: int, mode: str) -> None: ...      # "normal" or "fire"

In fire mode, which always hold:

- No lift moves up. Doors open only at floor 0, apart from the building letting riders out under
  the maintenance rule.
- From tick (fire start + floors + 2) onward, every lift in service must be at floor 0 and be given
  "open" on every tick until the mode returns to normal. A lift that returns to service during fire
  mode gets the same (floors + 2) ticks, counted from its return.
- When doors open at floor 0 in fire mode, all riders leave the building, whatever floor they
  pressed. They are finished: their car requests no longer apply, and they aren't counted in
  passenger times or limits.
- Nobody boards during fire mode. Hall calls can still reach you, and people keep waiting.
- When the mode returns to normal, every waiting person's hall call is sent to you again.

Design conditions: at most one fire in a run, starting between tick 60 and tick 479 and lasting
between 10 seconds and 2 minutes. The maintenance conditions still apply, and a lift may be out when
the fire starts and return during it.

Traffic envelope: the same as version 2. Time limit for everyone not evacuated: 590 s on days inside
this envelope and these conditions. Versions 1 to 3 must keep working.
