# Change request v5: the morning rush

From the building manager, verbatim: "Mornings are a mess. Between eight and five past, nearly
everyone arrives at the lobby at once. Keep the lifts at the lobby in the morning so people don't
wait."

What the building measures, which is the traffic envelope for this version: exactly 300 calls in the
first 5 minutes of a run, of which 240 go from floor 0 to an upper floor and 60 start on floors 1 to 29
and go to any other floor. The largest crowd is 6 people at one floor on one tick. The fastest arrivals
allowed are 25 calls in any 10 seconds and 85 in any 60 seconds, with no more than 25 of the upstairs
calls in any 60 seconds. All three lifts are in service and there is no fire during the rush.

On days inside this envelope:

- The 95th-percentile time of riders who board at the lobby is at or below 1760 s.
- Every rider who boards above the lobby still arrives within 190 s.
- Everyone arrives within 1850 s.

Versions 1 to 4 must keep working, including the ordinary day.
