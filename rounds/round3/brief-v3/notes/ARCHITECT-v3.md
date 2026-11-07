I read version 3 as one new fact per car: in service or not. The building evicts riders and they call again, so we don't rebuild them; we forget that car's requests and release its hall floors. The request doesn't say whether the event can repeat or name a bad lift; treat it as idempotent, never raise, and record that under Assumptions. Events precede step, so "stay" starts that tick.

Always true: an out car gets "stay" every tick, owns no hall floor and holds no car requests; no hall floor is lost; with every car in service, behaviour is exactly version 2.

Each car gains one state, out, reachable from any other; it returns idle and empty wherever floors_now says. Keep one flag per car, in modes/, and choose hall owners only among available cars.

Reviewer: teach the simulator eviction, with riders already at their floor counted arrived. Draw version 2 days with outages inside the conditions: one or two lifts, out from the first tick, out for the rest, both out together up to 2 minutes, a full car stopped mid-trip. Assert the worst passenger against 510 s, and rerun 270 s and 290 s. Fixed cases: out during an open, a hall call where an out car sits, a return while others are full.

The trap is a simulator that resets evicted riders' clocks, or outages drawn only at quiet moments. Done means DONE v3, three suites passing, worst time reported.
