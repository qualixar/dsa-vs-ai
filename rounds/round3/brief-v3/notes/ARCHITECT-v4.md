I read version 4 as one building-wide flag that overrides the sweep. In fire mode a car's command follows from availability and floor alone: out gets "stay", above floor 0 gets "down", at floor 0 gets "open". A non-stop descent beats floors + 2 ticks, so store no timer. Assumptions to record: a short fire can end with riders still aboard, so forget a car's requests only when it opens at floor 0 in fire; re-sent calls may arrive either side of the mode change, so keep recording hall floors throughout; repeated or unknown modes change nothing and never raise.

Always true in fire: no "up", "open" only at floor 0, and opening clears no hall floor because nobody boards. Without fire, behaviour is exactly version 3.

Keep the mode in modes/ beside availability. On return to normal choose hall owners afresh, since cars leave floor 0 together.

Reviewer: teach the simulator no boarding, evacuation, re-sent calls and its own deadline check, including returned lifts. Draw version 3 days with a fire starting between tick 60 and 479, lasting 10 seconds to 2 minutes, aimed at busy moments. Fixed cases: a car rising at fire start, the shortest fire catching a full car, a lift returning or removed mid-fire. Assert 590 s for everyone not evacuated; rerun 510, 290 and 270.

The trap is a simulator that calls riders evacuated when they weren't, deleting the worst times. Done means DONE v4, every suite passing, worst time reported.
