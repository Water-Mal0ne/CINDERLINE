# Harmonization evidence (review tasks A1-A5)

Data: REAL FIRMS DATA. Script: `python -m pipeline.review.harmonization_review` (no refitting, no re-selection).
Inputs: `reports/harmonization_eval.csv`, `reports/harmonization_model.json`, published national daily series in
`web/public/data/{country}.json`. Weekly = pandas W-MON weeks, the definition used by the official evaluation.

**Reproduction check.** Weekly test MAE, bias and correlation recomputed from the published daily series match the
official locked evaluation for every country and model available in published data (B0, B1, and M1 where selected);
see `layer1_reproduction_check.csv`.

## A1. Layer 1 table (2020-2024, weekly)

`layer1_table.md` / `layer1_table.csv`. Selected models (on 2018-2019 validation daily MAE): B1 for Australia,
Brazil and the United States; M1 for Bangladesh, Egypt, India and Nepal.

**Independent validation on NOAA-20 (review E3).** NOAA-20 VIIRS, converted with the saved S-NPP-fitted model and no refitting, matches the released converted S-NPP series in the test years 2020-2024: United States +1.3% (weekly r 0.984), Nepal +0.6% (r 0.989), Bangladesh -0.5% (r 0.987), Egypt -2.6% (r 0.829). Egypt's high bias against Aqua persists with NOAA-20 (+47.7%), which points at the Egypt ratio rather than at S-NPP. Details: `reports/review/noaa20/NOAA20.md`.

## A2. Per test year, selected model (weekly bias %, weekly correlation)

| Country | 2020 | 2021 | 2022 | 2023 | 2024 |
|---|---|---|---|---|---|
| Australia (B1) | +27.3%, 0.969 | +2.8%, 0.943 | +13.0%, 0.757 | +14.8%, 0.989 | -1.0%, 0.930 |
| Bangladesh (M1) | -1.7%, 0.984 | -4.6%, 0.987 | **+113.6%, 0.180** | +2.5%, 0.994 | -4.1%, 0.965 |
| Brazil (B1) | -1.3%, 0.971 | -9.5%, 0.989 | -13.6%, 0.977 | -12.3%, 0.990 | -14.4%, 0.981 |
| Egypt (M1) | +64.4%, 0.590 | +66.2%, 0.548 | +41.6%, 0.673 | +36.0%, 0.848 | +65.2%, 0.537 |
| India (M1) | +0.1%, 0.928 | -6.0%, 0.980 | +4.3%, 0.885 | -6.6%, 0.908 | -2.1%, 0.876 |
| Nepal (M1) | +4.5%, 0.985 | -14.6%, 0.978 | +4.9%, 0.955 | -9.2%, 0.963 | -6.3%, 0.988 |
| United States (B1) | +13.3%, 0.968 | +6.0%, 0.915 | +1.8%, 0.838 | -9.3%, 0.829 | -8.9%, 0.744 |

All models and years: `layer1_per_year.csv`. M1 per year is not available from published data for the three
B1-selected countries (their overall M1 test metrics are in A1).

What weakens the claim: Bangladesh 2022 is a failed year for the selected model; Egypt is biased high in every test
year; the US weekly correlation falls every year from 0.968 (2020) to 0.744 (2024) and the bias moves from +13% to
-9%; Brazil is biased low by 10-14% from 2021.

## A3. VIIRS-to-Aqua ratio by year, 2013-2024

National VIIRS detections per Aqua detection, days with both archives (`ratio_by_year.csv`, `ratio_trend.csv`,
`ratio_by_year.png`). Log-linear trend with a 2,000-draw year bootstrap:

| Country | Trend (%/year, 95% bootstrap range) | Mean 2013-2017 | Mean 2020-2024 | Test vs training |
|---|---|---:|---:|---:|
| Australia | -0.5 (-1.5 to +0.7) | 7.74 | 7.68 | -0.8% |
| Bangladesh | +0.2 (-3.1 to +5.2) | 4.85 | 5.17 | +6.6% |
| Brazil | -0.0 (-0.8 to +0.8) | 6.14 | 6.19 | +0.8% |
| Egypt | +4.0 (-3.5 to +11.7) | 24.5 | 34.0 | +38.9% |
| India | +0.6 (-0.1 to +1.0) | 7.91 | 8.03 | +1.6% |
| Nepal | -0.7 (-2.7 to +1.5) | 13.5 | 12.6 | -6.3% |
| United States | +0.8 (-0.9 to +3.0) | 6.30 | 6.94 | +10.0% |

Plainly: no country shows a trend that is distinguishable from zero with this year bootstrap. But the ratio in the
test years is higher than in training for Egypt (+39%) and the United States (+10%), which matches their test-year
problems in A2. Aqua's orbit drifted to a later crossing time in the early 2020s; these data cannot separate that
drift from real changes in fire timing or size.

## A4. Overlap charts

`aqua_vs_converted_viirs_Nepal.png`, `aqua_vs_converted_viirs_United_States.png`: weekly observed Aqua, converted
VIIRS (selected model) and raw VIIRS, 2013-2024, test years shaded. Aqua flew the whole time; the switch to
converted VIIRS from 2013 is a design choice for the future record (Aqua is near the end of its mission), and these
charts show how closely the converted series follows Aqua while both exist.

## A5. Distributions and anomaly flags

Overlap 2013-2024, weekly (`distribution_overlap.csv`):

| Country | Zero-week share, Aqua vs converted | p10 | p50 | p90 |
|---|---|---|---|---|
| Australia | 0.2% vs 0.2% | 434 vs 527 | 2,134 vs 2,237 | 4,708 vs 5,248 |
| Bangladesh | 33.5% vs 43.9% | 0 vs 0.01 | 2.0 vs 1.4 | 56.8 vs 42.6 |
| Brazil | 0.2% vs 0.2% | 407 vs 339 | 1,725 vs 1,411 | 10,411 vs 9,824 |
| Egypt | **9.4% vs 0.6%** | 1.0 vs 2.5 | 4.0 vs 5.9 | 14.0 vs 16.2 |
| India | 0.2% vs 0.2% | 12 vs 6.5 | 516 vs 412 | 2,948 vs 2,994 |
| Nepal | 32.2% vs 32.9% | 0 vs 0 | 6.0 vs 6.2 | 94 vs 101 |
| United States | 0.3% vs 0.2% | 334 vs 323 | 909 vs 795 | 2,143 vs 2,185 |

Anomaly flags (published, `anomaly_flags_by_period.csv`), 2003-2012 observed Aqua vs 2013-2024 converted VIIRS:

| Country | High flags (before / after 2013) | Low flags (before / after 2013) |
|---|---|---|
| Australia | 66 / 90 | 77 / 79 |
| Bangladesh | 84 / 66 | 25 / 50 |
| Brazil | 122 / 34 | 34 / 122 |
| Egypt | 41 / 113 | **100 / 38** |
| India | 75 / 80 | 73 / 80 |
| Nepal | 53 / 97 | 36 / 56 |
| United States | 94 / 62 | 58 / 98 |

Low flags pile up before 2013 in **Egypt** (100 vs 38), where converted VIIRS has almost no zero weeks and runs
higher than Aqua, so pre-2013 Aqua weeks look low against a history that includes the converted years. Brazil and
the US show the opposite (more lows after 2013); anomaly flags compare each week with all other years, so a real
long-term decline also produces this pattern, and the conversion's -10 to -14% Brazil bias adds to it.
