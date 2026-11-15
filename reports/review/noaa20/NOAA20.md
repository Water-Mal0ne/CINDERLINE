# NOAA-20 VIIRS as a separate-platform transfer check (review E3)

Data: REAL FIRMS DATA, NOAA-20 VIIRS 375 m, 2018-2024 (FIRMS archive name `viirs-jpss1`). This check is not part of the official decision or the released model.
Script: `python -m pipeline.review.noaa20_check NOAA20_DATA_DIR`.

**Countries analysed:** United States, Nepal, Bangladesh, Egypt. India, Australia and Brazil had not finished downloading when analysis was frozen.

**How the list is chosen:** those with all seven NOAA-20 years downloaded. The list is printed by the script and is the set of countries in `noaa20_conversion_check.csv`.

## (a) Conversion check

NOAA-20 detections are converted to the Aqua reference scale with the saved model. There is no refitting: each country uses the same model and ratios that were fitted on S-NPP. Weekly series are then compared on the held-out years 2020-2024.

| Country | Bias vs converted S-NPP | Weekly r | Bias vs Aqua (NOAA-20) | Bias vs Aqua (S-NPP) |
|---|---:|---:|---:|---:|
| United States | +1.3% | 0.984 | +3.5% | +2.2% |
| Nepal | +0.6% | 0.989 | -7.6% | -8.1% |
| Bangladesh | -0.5% | 0.987 | +6.2% | +6.8% |
| Egypt | -2.6% | 0.829 | +47.7% | +51.7% |

The S-NPP-vs-Aqua column is recomputed here on the same weeks as the NOAA-20 comparison. Days marked "no observation" (review E5) count as missing in this column, so it can differ slightly from the Layer 1 table (United States +2.2% here, +1.7% there).

The saved conversion transfers to a separate VIIRS platform without refitting in the reported countries. This is corroboration between related measurement products, not independent ground-truth validation. Egypt's high bias against Aqua appears with NOAA-20 too, but the shared discrepancy does not diagnose its cause.

A strict common-date outage sensitivity is still unfinished: a partly masked S-NPP week can be compared with a fuller NOAA-20 week. The separate season-preservation sensitivity does not resolve this NOAA-20 comparison's coverage limitation.

## (b) Fourth rhythm stream (reported separately, not in the gate)

The US Sunday dip appears in NOAA-20 too. For comparison, the official S-NPP VIIRS index is 0.782 over 2013-2024; NOAA-20 covers 2018-2024 only.

| Country | Rest day | Index on the rest day (95% CI) | Lowest day | p | Passes 0.05/21 |
|---|---|---|---|---|---|
| United States | Sun | 0.832 (0.798-0.870) | Sun | 0.0002 | yes |
| Nepal | Sat | 0.912 (0.825-0.988) | Fri | 0.108 | no |
| Bangladesh | Fri | 0.759 (0.631-0.863) | Thu | 0.032 | no |
| Egypt | Fri | 1.018 (0.982-1.062) | Thu | 0.833 | no |

The full tables are `noaa20_conversion_check.csv` and `noaa20_rhythm_stream.csv`.
