# NOAA-20 VIIRS as an independent check (review E3)

Data: REAL FIRMS DATA, NOAA-20 VIIRS 375 m, 2018-2024 (FIRMS archive name `viirs-jpss1`). This check is not part of the official decision or the released model.
Script: `python -m pipeline.review.noaa20_check NOAA20_DATA_DIR`.

**Countries analysed:** those with all seven NOAA-20 years downloaded. The list is printed by the script and is the set of countries in `noaa20_conversion_check.csv`.

## (a) Conversion check

NOAA-20 detections are converted to the Aqua reference scale with the saved model. There is no refitting: each country uses the same model and ratios that were fitted on S-NPP. Weekly series are then compared on the held-out years 2020-2024.

| Country | Bias vs converted S-NPP | Weekly r | Bias vs Aqua (NOAA-20) | Bias vs Aqua (S-NPP) |
|---|---:|---:|---:|---:|
| Nepal | +0.6% | 0.989 | -7.6% | -8.1% |
| Bangladesh | -0.5% | 0.987 | +6.2% | +6.8% |
| Egypt | -2.6% | 0.829 | +47.7% | +51.7% |

The saved conversion carries over to a second VIIRS satellite without refitting. Egypt's high bias against Aqua appears with NOAA-20 too, which points at the Egypt ratio rather than at S-NPP.

## (b) Fourth rhythm stream (reported separately, not in the gate)

| Country | Rest day | Index on the rest day (95% CI) | Lowest day | p | Passes 0.05/21 |
|---|---|---|---|---|---|
| Nepal | Sat | 0.912 (0.825-0.988) | Fri | 0.108 | no |
| Bangladesh | Fri | 0.759 (0.631-0.863) | Thu | 0.032 | no |
| Egypt | Fri | 1.018 (0.982-1.062) | Thu | 0.833 | no |

The full tables are `noaa20_conversion_check.csv` and `noaa20_rhythm_stream.csv`.
