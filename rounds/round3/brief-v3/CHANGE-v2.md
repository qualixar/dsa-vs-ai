# Change request v2: three lifts

The building now has three lifts. `Dispatcher(floors, lifts)` is constructed with lifts=3 and `step`
returns three commands. The three lifts share the hall calls; a hall call is for the floor, not for a
lift, so any lift may answer it.

Traffic envelope: exactly 120 calls in the first 10 minutes of a run, from any floor to any other, mostly
at random times. Some days bring a crowd at one floor on one tick, or a burst of thirty calls in ten
seconds; those people are among the 120. The largest crowd is 15 people. The fastest arrivals allowed
are 35 calls in any 10 seconds, 50 in any 60 seconds and 90 in any 5 minutes.

Time limit: 290 s for every passenger on days inside this envelope. Version 1 must keep working.
