# Rhythm test credibility checks (review B1-B5)

Data: REAL FIRMS DATA, 2013-2024, seven countries. Script: `python reference/rhythm_review.py data OUT_DIR`
(imports `reference/kill_test.py` unchanged; outputs in `reports/review/rhythm/`). None of these checks changes the
official pre-specified decision (pass).

## B1. Monte Carlo precision (200,000 null draws, seed 20261114)

`b1_monte_carlo_200k.csv`. The official run uses 5,000 draws, so its smallest possible p-value is 0.0002. With
200,000 draws no significance call changes (threshold 0.05/21 = 0.00238, plus rest day lowest).

| Country | Stream | Exceedances / 200,000 | p | Monte Carlo SE | Official p (5,000) | Call |
|---|---|---:|---:|---:|---:|---|
| United States | Terra, Aqua, VIIRS | 0 each | 0.000005 | 0.000005 | 0.0002 | significant, unchanged |
| Australia | Terra | 288 | 0.00145 | 0.00009 | 0.0018 | significant, unchanged |
| Australia | Aqua | 0 | 0.000005 | 0.000005 | 0.0002 | significant, unchanged |
| Australia | VIIRS | 5 | 0.00003 | 0.00001 | 0.0002 | significant, unchanged |
| Brazil | Terra | 0 | 0.000005 | 0.000005 | 0.0002 | significant, unchanged |
| Brazil | Aqua | 69 | 0.00035 | 0.00004 | 0.0002 | significant, unchanged |
| Brazil | VIIRS | 108 | 0.00055 | 0.00005 | 0.0002 | not significant (Sunday not the lowest day), unchanged |
| Bangladesh | VIIRS | 70 | 0.00036 | 0.00004 | 0.0008 | significant, unchanged |
| India, Nepal, Egypt, other Bangladesh streams | all | - | 0.07-0.98 | <0.0012 | same | not significant, unchanged |

Australia Terra is the closest call (p = 0.00145 against a threshold of 0.00238).

## B2. Leave one year out (passing countries)

`b2_leave_one_year_out.csv`, `b2_leave_one_year_out_summary.csv`. Rest-day index range when each of the 12 years is
dropped in turn:

| Country | Terra | Aqua | VIIRS | Rest day still lowest every time? |
|---|---|---|---|---|
| United States | 0.709-0.738 | 0.655-0.685 | 0.773-0.789 | yes, all streams |
| Australia | 0.928-0.949 | 0.885-0.904 | 0.932-0.944 | yes, all streams |
| Brazil | 0.883-0.905 | 0.911-0.928 | 0.933-0.946 | Terra and Aqua yes; **VIIRS no in 11 of 12** (Monday lower) |

No single year drives any passing result.

## B3. Weekday shapes

See `weekday_shapes.md`. US: Saturday also below average, Tuesday-Thursday above. Australia and Brazil: Monday is
also below average (no Monday rebound; the low runs Sunday into Monday). No rest day is significantly above average
anywhere; Nepal Aqua's Saturday 1.264 has an interval that includes 1.

## B4. Negative control split by type

`b4_controls_by_type.csv`. Type 2 (other static land sources) is flat in every country with enough data (US, Australia,
Brazil, India, Egypt, Bangladesh VIIRS); none significant. Type 1 (volcano) has enough data only in the United States,
and there **US type-1 VIIRS shows a Sunday dip** (index 0.861, 95% interval 0.755-0.958, p = 0.0012, significant at
0.05/21; 11 years, 42,920 detections); US type-1 Terra is lower on Sunday but not significant, Aqua is not. Volcanic
heat has no reason to follow a work week, so this either reflects vegetation fires near volcanoes being typed as
volcanic, or a weekly pattern we cannot explain. It weakens the use of the US control as evidence against an
observational artifact, although the much larger type-2 control (887,094 VIIRS detections) is flat.

## B5. Nepal power

`b5_nepal_power.csv` (labelled SYNTHETIC PLANTED DIP ON REAL NEPAL VOLUME). Real Nepal daily counts per stream; in each
of 200 simulations every year's weekday labels are shifted by a random 0-6 days (keeps volume, seasonality and
clustering, removes any real weekly signal), then a Saturday dip is planted by thinning Saturday detections. The
official rule is applied.

| Planted Saturday dip | Country passes | Terra significant | Aqua significant | VIIRS significant |
|---|---:|---:|---:|---:|
| none | 0.5% | 0.5% | 0.5% | 0.5% |
| 10% | 0.0% | 2.0% | 2.0% | 13.5% |
| 20% | 12.0% | 6.0% | 7.0% | 84.5% |

So: Nepal is too small to tell under the country rule; the MODIS streams almost never detect even a 20% dip. VIIRS
alone would have detected a 20% Saturday dip 85% of the time, and Nepal's real VIIRS Saturday index is 1.015, so a dip
of 20% or more in VIIRS-detected burning is unlikely; a 10% dip could easily have been missed.
