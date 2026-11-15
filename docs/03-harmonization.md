# Harmonization

CINDERLINE converts archived VIIRS S-NPP detections onto the MODIS Aqua reference scale. The result is an estimate of Aqua-equivalent detections. It does not recover undetected burning, count individual events, or measure burned area.

The historical series uses observed Aqua for 2003-2012 and converted VIIRS for 2013-2024. The calendar also has a frozen-model extension for 2025, beyond the evaluated period. The annual globe ends in 2024. These scopes are recorded in the [model](../reports/harmonization_model.json), [2025 report](../reports/review/extend2025/CONTINUITY.md) and [annual alignment report](../reports/calendar-confidence/OUTAGE_ALIGNMENT.md).

## From archived rows to daily counts

The [cleaning code](../pipeline/clean.py) keeps each instrument stream separate. MODIS records need numeric confidence of at least 30; VIIRS records need nominal or high confidence. Invalid acquisition timestamps, out-of-range coordinates and unresolved timezones are excluded and counted in diagnostics. Unknown source type stays unknown. The calendar and calibration use vegetation detections, type 0; other types are retained for separate checks. These rules are also described in [Methods](../METHODS.md).

UTC acquisition times become local civil times before assigning a date, weekday or year. Nepal, India, Bangladesh and Egypt use their configured IANA zones. For the United States, Brazil and Australia, the code looks up the zone at each detection's coordinates. Daylight-saving rules come from that zone. It does not infer a timezone from a rounded map cell.

Detections are assigned to a 0.25-degree latitude/longitude grid. A cell's southwest corner is:

```text
grid_latitude  = floor(latitude  / 0.25) * 0.25
grid_longitude = floor(longitude / 0.25) * 0.25
```

This grid is an aggregation unit, not the instrument's pixel footprint. Cells have different ground areas at different latitudes. Daily counts retain country, cell, date, instrument, day/night class and reported FRP class. National totals include all qualifying cells; the 12 daily drill-down cells per country are selected from training-period activity. They do not limit the national calculation. See the [model and selection metadata](../reports/harmonization_model.json) and [aggregation code](../pipeline/harmonize.py).

Archive availability and observation coverage are different. The original build requires adjacent UTC annual archives to support a complete local year, because records near New Year can change year during timezone conversion. This makes 2013 the first eligible VIIRS year in this build. A verified archive with no qualifying records can yield zero; a missing archive or excluded observation period stays unavailable. Neither a verified archive nor a zero count proves cloud-free observation. See [Methods](../METHODS.md).

## The reference and overlap period

Aqua supplies the named reference scale and the earlier observed record. Keeping one named MODIS stream makes the target explicit; Terra remains a separate stream instead of being added to Aqua. Aqua also overlaps the VIIRS record, so its observations can be compared with converted VIIRS on dates when both archives exist. The switch in the displayed series is a product choice, not a claim that Aqua stopped operating in 2013. See the [overlap review](../reports/review/HARMONIZATION_REVIEW.md).

Aqua and VIIRS have historically had similar afternoon crossing schedules, while Terra's daytime crossing is in the morning. That makes Aqua the closer timing reference, although the observations are not simultaneous and Aqua's orbit has drifted. [NASA's transition guidance](https://ladsweb.modaps.eosdis.nasa.gov/learn/modis-to-viirs-transition) describes that distinction.

The conversion is learned from aggregate counts. It does not pair individual detections across sensors or guarantee matching overpasses. Aqua is an observation reference, not ground truth. Differences in pixel size, detection sensitivity, timing, cloud and instrument behavior remain in the comparison. The [limitations](../LIMITATIONS.md) apply to both the conversion and its evaluation.

The model has separate roles for each period:

| Period | Use |
| --- | --- |
| 2013-2017 | Fit conversion ratios |
| 2018-2019 | Select B1 or M1 for each country using daily mean absolute error |
| 2020-2024 | Report held-out performance without changing the selection |
| 2025 | Apply the saved model as a later continuity check |

The [saved model](../reports/harmonization_model.json) records the first three periods. The [evaluation runner](../pipeline/streaming/evaluate_counts.py) saves the choices before evaluating the test years. Later reviews of those test years are retrospective checks, not fresh holdouts.

## B0, B1 and M1

Let `V(c,d,s)` be the VIIRS detection count for country `c`, local date `d` and stratum `s`. Let `A_train` and `V_train` be Aqua and VIIRS training counts across the declared training countries. Strata combine country, day/night and reported FRP: below 10 MW, 10 to below 50 MW, at least 50 MW, or unknown. The formulas and constants below come from [the model implementation](../pipeline/harmonize.py) and [Methods](../METHODS.md).

| Model | Daily estimate | Meaning |
| --- | --- | --- |
| B0 | `sum_s V(c,d,s)` | Raw VIIRS count, with no conversion |
| B1 | `r * sum_s V(c,d,s)`, where `r = A_train / V_train` | One ratio shared by all training countries |
| M1 | `sum_s r(c,s) * V(c,d,s)` | A country/stratum ratio with a fallback toward B1 |

M1 uses:

```text
r(c,s) = [A_train(c,s) + 100 * r] / [V_train(c,s) + 100]
```

The fixed 100-detection pseudo-count pulls sparse strata toward the global ratio. A missing fitted stratum uses B1. The seven-country B1 ratio is `0.1450130601167073`, from the [saved parameters](../reports/harmonization_model.json). Adding training countries changes this ratio and M1's shrinkage target; older two-country results are a different fitted scope.

M1 wins only when its validation daily MAE is lower than B1's. Ties retain B1. B0 is reported as an unconverted baseline and is never selected as the conversion. The split and selection rule are fixed in the [evaluation code](../pipeline/streaming/evaluate_counts.py).

These are empirical count weights. FRP classes are based on each instrument's reported value, not on physically identical sampled areas or energy. Some weights exceed one. A converted count may be fractional because it is an estimate on a reference scale, rather than a list of retained or deleted detection records.

## What the metrics measure

For paired periods `t`, let `a_t` be observed Aqua and `h_t` the estimate. The [metric implementation](../pipeline/harmonize.py) uses finite paired values:

```text
bias (%) = 100 * [sum_t h_t - sum_t a_t] / sum_t a_t
MAE      = sum_t abs(h_t - a_t) / n
r        = sum_t [(a_t - mean(a)) * (h_t - mean(h))]
           / sqrt[sum_t (a_t - mean(a))^2 * sum_t (h_t - mean(h))^2]
```

Bias describes disagreement in the total; positive bias means the converted total is higher. MAE is the average size of a period's error in detection-equivalent units. Pearson `r` describes how the two series vary together. High correlation can coexist with a large bias. Correlation is undefined for a constant series, and percentage bias is undefined when the reference sum is zero.

The official weekly evaluation uses pandas `W-MON` bins, weeks ending on Monday. The display calendar's Jan-1-anchored bins are a separate grouping. Monthly and weekly metrics are not interchangeable. See [the evaluation code](../pipeline/harmonize.py) and [calendar code](../pipeline/calendar.py).

## Layer 1 results

The full [locked Layer 1 table](../reports/review/layer1_table.md) retains B0, B1 and M1 for every country. Selection uses daily MAE on 2018-2019; the test columns report weekly results on 2020-2024. Weekly MAE is in Aqua-reference-equivalent detections per week. B0 is an unconverted baseline, so its selection and validation-choice entries are blank. The test results did not choose the selected model.

| Country | Model | Selected | Validation daily MAE | Test bias (%) | Test weekly MAE | Test weekly r |
| --- | --- | --- | ---: | ---: | ---: | ---: |
| Australia | B0 |  |  | +665.7 | 15,767.9 | 0.962 |
| Australia | B1 | yes | 134.19 | +11.0 | 514.9 | 0.962 |
| Australia | M1 |  | 173.40 | -2.6 | 776.1 | 0.925 |
| Bangladesh | B0 |  |  | +357.1 | 127.1 | 0.926 |
| Bangladesh | B1 |  | 4.28 | -33.7 | 18.3 | 0.926 |
| Bangladesh | M1 | yes | 4.27 | +6.8 | 12.1 | 0.921 |
| Brazil | B0 |  |  | +517.3 | 22,343.7 | 0.979 |
| Brazil | B1 | yes | 119.43 | -10.5 | 694.3 | 0.979 |
| Brazil | M1 |  | 122.67 | +5.4 | 950.2 | 0.975 |
| Egypt | B0 |  |  | +3135.7 | 175.8 | 0.790 |
| Egypt | B1 |  | 3.09 | +369.2 | 20.7 | 0.790 |
| Egypt | M1 | yes | 0.87 | +51.7 | 4.3 | 0.729 |
| India | B0 |  |  | +702.1 | 7,183.9 | 0.903 |
| India | B1 |  | 82.49 | +16.3 | 377.4 | 0.903 |
| India | M1 | yes | 70.92 | -2.4 | 337.9 | 0.930 |
| Nepal | B0 |  |  | +1167.2 | 566.7 | 0.966 |
| Nepal | B1 |  | 6.16 | +83.8 | 43.3 | 0.966 |
| Nepal | M1 | yes | 3.73 | -8.1 | 11.3 | 0.977 |
| United States | B0 |  |  | +601.4 | 7,298.4 | 0.905 |
| United States | B1 | yes | 57.43 | +1.7 | 390.8 | 0.905 |
| United States | M1 |  | 69.37 | +12.9 | 514.8 | 0.884 |

The US total is close to Aqua across the full test period, but its weekly correlation falls from 0.968 in 2020 to 0.744 in 2024. Its yearly bias shifts from +13.3% to -8.9%. Bangladesh's 2022 result is +113.6% bias with `r = 0.180`. Egypt stays biased high in every test year. These failures are visible in the [per-year review](../reports/review/HARMONIZATION_REVIEW.md); the pooled table does not remove them.

Bangladesh's validation choice is also narrow: M1 daily MAE is 4.27 against B1's 4.28, at the precision shown in [Layer 1](../reports/review/layer1_table.md). This is the saved rule's outcome, not evidence of a large advantage.

## Season shape and local accuracy

Matching totals does not ensure matching seasonal shape. A retrospective experiment replaces Aqua with each VIIRS alternative on the same retained dates, without refitting. Monthly-share disagreement uses total variation:

```text
TV = 0.5 * sum_month abs(estimated_month_share - Aqua_month_share)
```

For India's whole-year replacement, the primary common outage mask gives mean absolute annual count disagreement of 13.8349% for B1 and 4.0537% for selected M1. Monthly-pattern disagreement moves the other way, from 12.3145 to 15.5725 points of `TV * 100`. Nepal improves on both measures: count disagreement falls from 77.6713% to 8.3035%, and monthly TV from 13.8237 to 5.7534 points. These are equally weighted averages over 2020-2024, using retained dates rather than complete annual observation coverage. Both directions survive the padded-mask check. See the [season report](../reports/review/season/SEASON_CHECK.md).

National agreement also does not establish local accuracy. The separate grid diagnostic holds geography and weights fixed while comparing 0.25-degree cells with 0.5-degree parents on 2018-2019. US normalized monthly absolute error is 145.94% versus 144.35%; Egypt is 178.77% versus 145.25%. Coarsening can cancel opposing errors. The diagnostic covers selected geography and reuses validation years. It does not validate arbitrary local areas. See [the grid results](../reports/scientific_validation/grid_sensitivity.csv) and [selection lock](../reports/scientific_validation/grid_selection_lock.json).

## Transfer to NOAA-20

The separate NOAA-20 check applies the saved S-NPP conversion without refitting. Four countries had complete downloaded inputs when that analysis was frozen. The comparison below covers 2020-2024. India, Brazil and Australia were not evaluated in this check. See [the NOAA-20 report](../reports/review/noaa20/NOAA20.md).

| Country | NOAA-20 bias versus converted S-NPP | Weekly r versus converted S-NPP | NOAA-20 bias versus Aqua |
| --- | ---: | ---: | ---: |
| United States | +1.3% | 0.984 | +3.5% |
| Nepal | +0.6% | 0.989 | -7.6% |
| Bangladesh | -0.5% | 0.987 | +6.2% |
| Egypt | -2.6% | 0.829 | +47.7% |

The related VIIRS platforms agree more closely with each other than Egypt agrees with Aqua. This is a transfer check between instruments, not independent ground-truth validation. It does not identify the cause of Egypt's mismatch.

This comparison still lacks a strict common-date outage sensitivity: a partly excluded S-NPP week can be compared with a fuller NOAA-20 week. Its recomputed S-NPP-versus-Aqua US bias is +2.2%, rather than Layer 1's +1.7%, because its dates and missing-value treatment differ. These results should keep their source labels.

## The 2025 continuity extension

The saved model is applied to S-NPP detections without new fitting or selection. The [2025 continuity report](../reports/review/extend2025/CONTINUITY.md) compares weekly national estimates with Aqua after excluding no-observation days on both sides:

| Country | 2025 bias versus Aqua | 2025 weekly r |
| --- | ---: | ---: |
| Australia | +16.4% | 0.982 |
| Bangladesh | -6.6% | 0.987 |
| Brazil | -21.4% | 0.962 |
| Egypt | +50.0% | 0.305 |
| India | -11.1% | 0.942 |
| Nepal | -17.6% | 0.987 |
| United States | -7.0% | 0.845 |

Brazil and Nepal move further below Aqua than in the held-out years. Egypt's timing comparison also deteriorates; its Aqua reference contains only 237 detections in 2025. These data do not separate changes in the instrument, processing, orbit or burning conditions.

No calibration interval was computed for 2025, so its interval fields are empty. Historical season statistics, anomaly flags, model evaluation and rhythm results keep their original periods. The report also marks 12 November 2025 as unavailable in Australia, Bangladesh, Egypt, India and Nepal, and warns that the western-hemisphere end of the year lacks the following UTC archive needed for late local detections.

## Outages, uncertainty and remaining limits

The calendar marks known supplier outages and previously flagged all-country zero-record dates as "no observation". Their values are null, and affected weeks are excluded from season statistics and anomaly flags. A zero on an eligible day still means no qualifying archived detections, not verified observation of no activity. Exact exclusions are implemented in [the outage treatment](../pipeline/review/no_observation.py).

The original held-out evaluation is frozen and was not recomputed after these display exclusions. Aqua outages during test years can therefore affect the reference and apparent errors. The newer season check applies the same mask to both instruments; the NOAA-20 check still has the coverage limitation described above.

The current annual globe uses a separately verified correction for 5,756 affected cell-years, covering contributions from 57,938 archived detections. Its displayed totals align with available daily calendar values; the original globe source file remains unchanged. Custom-area monthly data instead omit whole months containing exclusions, so those totals have different temporal support. See [the alignment report](../reports/calendar-confidence/OUTAGE_ALIGNMENT.md).

For the evaluated converted record, the band is the 2.5th-to-97.5th percentile of estimates from 200 resamples of whole training years. Each draw refits the ratios; the selected model remains fixed. It describes sensitivity of calibration to the available training years. It omits cloud and overpass exposure, day-to-day conversion error, local spatial error and model-selection uncertainty. On observed-Aqua dates both bounds equal the observed count because no conversion is applied, not because the instrument is certain. See [Methods](../METHODS.md) and [the bootstrap implementation](../pipeline/harmonize.py).

Other limits remain relevant:

- Egypt's converted series has fewer zero weeks than Aqua in the overlap review, 0.6% against 9.4%. A positive ratio cannot remove VIIRS detections that Aqua misses, and historical anomaly comparisons can inherit that difference. These are frozen review statistics, not new counts of the current displayed anomaly flags. See [the distribution review](../reports/review/HARMONIZATION_REVIEW.md).
- The mean peak-week error in the locked evaluation is 17.6 weeks in Egypt, 10.0 in the US and 7.0 in India. Aggregate bias does not measure this timing error. See [the evaluation CSV](../reports/harmonization_eval.csv).
- The VIIRS-to-Aqua ratio is 38.9% higher in Egypt's test years than its training years and 10.0% higher in the US. The year-bootstrap trend intervals still include zero. The review cannot isolate Aqua's late-mission drift from other changes. See [the ratio review](../reports/review/HARMONIZATION_REVIEW.md).
- MODIS archive version fields change across fitting, selection and test periods. That processing change is not isolated by the current calibration. See [Methods](../METHODS.md) and [limitations](../LIMITATIONS.md).
- There is no published pre-Aqua reconstruction. A separate Terra bridge experiment improves count MAE but its ratio-only intervals contain Aqua in only 8.3-22.2% of active validation months. It does not justify extending the product back before its supported record. See [the bridge validation](../reports/scientific_validation/terra_bridge_validation.csv).
