"""Do new inputs help the model? Training years only (2022-08-04 to 2024-12-31); 2025 is never read.

THE RULE, committed before any of these inputs was built or scored:

Inputs tried (all known by the evening before the target day):
  a  naqfc_tomorrow: NOAA NAQFC's forecast for the target day (data/naqfc_dayahead.csv), from the 12Z run
     the day before (about 6 AM Central). 18 training city-days (3 run days) have none: we fill them with
     today's reading (obs_1), for both models. None of the 2025 rows is missing.
  b  today's EPA readings in a ring of 14 metros around our six, from the same EPA daily files:
     Duluth, Fargo, Bismarck, St. Cloud, Sioux Falls, Rochester MN, Des Moines, Cedar Rapids, Green Bay,
     Grand Rapids, Lansing, Indianapolis, Kansas City, Omaha. (The list given in our plan; Grand Forks was on it
     but has no PM2.5 monitor in the EPA files.) Three columns: ring_max_today, ring_mean_today (over the metros
     with a reading that day), and north_max_today = the highest of the 4 ring metros north of 45°N
     (Duluth, Fargo, Bismarck, St. Cloud), the first ones Canadian smoke crosses. Every day has at least one
     ring metro and one north metro, so no filling is needed.
  c  evening_today: this city's mean of EPA hourly readings from 2 PM to 7 PM local standard time today
     (hours starting 14:00 to 18:00; 3-8 PM in summer daylight time, so known by 8 PM). From EPA's hourly files
     (hourly_88101_YYYY.zip). City-days with no hourly reading in that window are filled with obs_1.

Variants, each the notebook's Ridge + trees average with these inputs appended after the current ones:
  current, +a, +b, +c, +a+b, +a+b+c

How they are compared: the notebook's training rows (2022-08-07 to 2024-12-31, 5,268 city-days), the same rows
for every variant; leave-one-block-out (2022 Aug-Dec, 2023, 2024), each block predicted by a model trained on
the other two. Average error (MAE, 2 decimals) and warning cost (5 x missed + false alarms) at the cut-off from
the notebook's best_cut_off (median over 200 week-resampled copies, seed 0) on the out-of-fold forecasts.
The current model must reproduce MAE 2.49 and cost 117 (cut-off 24.5, 19 missed, 22 false alarms).

Decision: take the variant with the lowest MAE (a tie at 2 decimals goes to the one with fewer inputs).
Adopt it only if its MAE is at most 2.44 (at least 0.05 below 2.49) AND its cost is at most 122
(not more than 5 above 117). Otherwise nothing is adopted: we do not fall back to the runner-up.
Warning counts are noisy (38 bad days, mostly one event); the average error is the steady number.
If one is adopted, 2025 is scored exactly once with it. If none is, 2025 is not scored for any variant.

Run:  python compare_features.py
"""
