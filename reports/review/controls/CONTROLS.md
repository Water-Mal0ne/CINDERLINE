# Static-source controls: year-level recheck

Data: REAL FIRMS DATA. These are robustness checks and don't change the official decision.
Script: `python -m pipeline.review.control_check ../firetrace/data`.

**Method.** This is the official rhythm method. Each complete year with at least 140 detections gives a weekday index (counts divided by weekday exposure, normalised to a mean of 1). Each country's index is the mean over those years. The 95% CI comes from a year bootstrap. The p-value comes from the random-weekday null with 200,000 draws, with Bonferroni 0.05/21 and at least 5 years required. Counts are not pooled across years.

**Inputs.**
- 2002-2024: `data/sample/seven_country_rhythm_counts.parquet`, with eligible years as used in the 2002-2024 robustness run.
- Locating volcano detections: the raw FIRMS country CSVs for 2013-2024.

## US volcano (type 1)

**Years with enough detections:** 11 for VIIRS (2013-2024, missing 2020), 5 for Terra and 5 for Aqua (2018 and 2021-2024). There are no type-1 detections before 2013.

**Where the detections come from.**
- Kilauea: 95% of VIIRS volcano detections (40,680 of 42,920), mostly its lava-lake activity in 2013-2017 and 2022-2023.
- The 2018 eruption year has 1,770 VIIRS detections and the deepest single-year Sunday index (0.551).
- Mauna Loa's December 2022 eruption is the largest month in Terra and Aqua.
- Alaska and the Aleutians: 2,156 VIIRS detections.

| Test | Sunday index (95% CI) | p | Passes 0.05/21 |
|---|---|---|---|
| VIIRS, all years | 0.861 (0.749-0.956) | 0.0011 | yes |
| VIIRS without its largest year (2017) | 0.845 (0.727-0.950) | 0.0005 | yes |
| VIIRS without the 2018 Kilauea eruption | 0.891 (0.787-0.975) | 0.0071 | no |
| VIIRS, Hawaii only | 0.848 | 0.0011 | yes |
| VIIRS, Alaska only (6 years) | 0.984, lowest day Sat | 0.45 | no |
| Terra (5 years) | 0.812 (0.607-0.943) | 0.026 | no |
| Aqua (5 years) | 1.009, lowest day Sat | 0.58 | no |
| US type 2 (industrial), Terra / Aqua / VIIRS, 2002-2024 | 1.001 / 1.032 / 1.010 | 0.53 / 0.95 / 0.86 | no |

**Reading.** The volcano dip is an unexplained single-volcano, single-satellite result. A processing or satellite artifact would be expected to appear across satellites and source types.

## Brazil type 2 (industrial), Terra

| Period | Sunday index (95% CI) | p | Passes 0.05/21 |
|---|---|---|---|
| 2002-2024 (23 years), as flagged | 0.913 (0.843-0.981) | 0.0009 | yes |
| 2002-2024 without its largest year (2004) | 0.923 (0.854-0.993) | 0.0024 | no |
| 2002-2007 | 0.745 (0.668-0.848) | 0.0001 | yes |
| 2008-2024 | 0.973 (0.907-1.040) | 0.17 | no |
| 2013-2024 (official window) | 0.966 (0.887-1.049) | 0.15 | no |

The Brazil Aqua and VIIRS industrial controls do not pass in either period.

Per-year rows are in `control_recheck_per_year.csv`; locations are in `us_volcano_*.csv`.
