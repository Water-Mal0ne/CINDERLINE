# Weekly Rhythm Index

The rhythm analysis asks whether archived vegetation detections are systematically lower on a country's pre-specified rest day. It uses raw Terra MODIS, Aqua MODIS and VIIRS S-NPP separately. No harmonization weights enter this calculation.

A repeating weekday pattern is consistent with scheduled human activity. It cannot identify who was responsible, establish why burning occurred, or assign a cause to an individual event. The same event can appear in several instruments, so agreement across streams is corroboration rather than independent replication. These limits are recorded with the [official decision](../reports/official/kill_test_gate.json).

The original rule was pre-specified, with a limited chronology: US and Nepal data were already available, and no Git record predates the first real-data analysis. The rule preceded acquisition for the other countries. Its local-file timeline is preserved in [the decision record](../DECISIONS.md#gate-timeline-review-b6-14-november-2026-nepal-time); it is not evidence of an externally registered prospective study.

## The index

For year `y` and weekday `w`, let `C(y,w)` be its qualifying detection count and `E(y,w)` the number of calendar occurrences of that weekday. The [official implementation](../reference/kill_test.py) computes:

```text
rate(y,w)  = C(y,w) / E(y,w)
index(y,w) = rate(y,w) / mean_over_weekdays(rate(y,w))
index(w)   = mean_over_eligible_years(index(y,w))
```

Dividing by weekday occurrences corrects for some weekdays occurring 53 times rather than 52. Averaging yearly indices equally prevents a high-count year from dominating the result. An index of 1 is the mean weekday rate; 0.8 is 20% below it. This denominator counts calendar opportunities, not measured clear-sky observation exposure.

The official study window is 2013-2024. A usable year needs at least 140 detections and at least 95% of its records assigned to the matching archive year after local-time conversion; at least 5 usable years are required. The archive-year rule removes partial edge years. It does not prove complete daily observation coverage. See [the engine](../reference/kill_test.py), [official results](../reports/official/kill_test_results.csv) and [diagnostics](../reports/official/kill_test_diagnostics.json).

The original rhythm engine and the calendar cleaner have different input rules. For multi-zone countries, [the original engine](../reference/kill_test.py) looks up timezones after rounding coordinates to 0.1 degree; [the calendar cleaner](../pipeline/clean.py) uses exact coordinates. The original engine also treats a missing hotspot type as vegetation, while the calendar cleaner preserves it as unknown. These code differences do not quantify an error in the saved results, but prevent describing the two cleaning paths as identical.

## Uncertainty and the pass rule

The interval resamples whole yearly weekday profiles, keeping all weekday values from each sampled year together. The official run uses 2,000 bootstrap draws and reports the 2.5th and 97.5th percentiles. This retains within-year dependence instead of pretending each detection is an independent experiment. It still relies on a small set of years. See [the test implementation](../reference/kill_test.py).

The random-weekday null asks how low the pre-specified day looks compared with choosing a random weekday separately in each year. For each of 5,000 draws, the test selects one weekday index from each year's profile and averages those choices. Its one-sided p-value is:

```text
p = [1 + number of null means <= observed rest-day mean] / [5000 + 1]
```

The plus-one correction prevents a reported p-value of zero. This is a random-weekday reference test; it does not simulate satellite exposure, weather or ignition causes.

The official analysis has 21 country-stream tests. A stream passes when its pre-specified day is the lowest weekday and its raw null-test `p < 0.05 / 21`, about 0.00238. Equivalently, its Bonferroni-adjusted p-value must be below 0.05. The displayed bootstrap interval is not an extra criterion in this official rule. A country needs at least 2 passing streams. The overall gate requires the US replication check and at least 2 other countries. See [the implementation](../reference/kill_test.py) and [official gate](../reports/official/kill_test_gate.json).

The original code sets the correction-family size to the number of country-stream rows with sufficient data; all 21 qualify in the saved official run. Its lowest-day comparison accepts a tie for the minimum. These details differ from the later pipeline's fixed-family and additional interval requirements.

## Results across the countries

The table gives the pre-specified day's index for the all-day analysis, directly from [the official results CSV](../reports/official/kill_test_results.csv). "Pass" refers to the country rule above, not to proof of a cause.

| Country | Pre-specified day | Terra index | Aqua index | VIIRS index | Passing streams | Country result |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| United States | Sunday | 0.723 | 0.667 | 0.782 | 3/3 | Pass |
| Australia | Sunday | 0.936 | 0.890 | 0.937 | 3/3 | Pass |
| Brazil | Sunday | 0.892 | 0.922 | 0.941 | 2/3 | Pass |
| India | Sunday | 1.022 | 0.949 | 1.003 | 0/3 | Does not pass |
| Nepal | Saturday | 0.891 | 1.264 | 1.015 | 0/3 | Does not pass |
| Bangladesh | Friday | 0.814 | 0.912 | 0.727 | 1/3 | Does not pass |
| Egypt | Friday | 1.045 | 1.088 | 1.036 | 0/3 | Does not pass |

The [official overall decision is pass](../reports/official/kill_test_gate.json). All passing countries have Sunday as their pre-specified day. The results therefore do not establish that the method recovers different national rest days.

Brazil illustrates why both criteria matter. Its VIIRS Sunday index is below 1 and has a small null-test p-value, but Monday is lower, 0.933 versus Sunday's 0.941. That stream fails the lowest-day requirement. Bangladesh's Friday signal passes only in VIIRS. Its other streams do not confirm it. India, Nepal and Egypt do not establish the predicted national dip under this rule.

The all-day and daytime analyses are separate. US daytime indices are 0.630 for Terra, 0.646 for Aqua and 0.657 for VIIRS. Those are not the same estimates as the all-day row or the later FRP comparison, which uses paired measures on retained dates. See [the official CSV](../reports/official/kill_test_results.csv).

## Checks after the official analysis

Rerunning the null test with 200,000 draws changes no significance call. Leaving each year out in turn keeps Sunday lowest for all US and Australian streams. Brazil remains supported by Terra and Aqua; Sunday is not VIIRS's lowest day in 11 of the 12 leave-one-year-out runs. See [the review](../reports/review/RHYTHM_REVIEW.md).

A separate, stricter pipeline result reports `statistical_decision: pass` but `decision: insufficient_data` and `production_allowed: false`. It uses additional requirements for country-matched controls and a different available-year scope, including a longer MODIS record. Brazil's control is flagged there. That output is preserved in [the stricter gate](../reports/kill_test_gate.json); it must not be substituted for the [official gate](../reports/official/kill_test_gate.json), or omitted when discussing controls.

The stricter stream rule requires verified local-year archive support, a rest-day bootstrap upper bound below 1, the lowest-day condition and a corrected p-value below 0.05. It retains the 21-test correction family even when some streams lack sufficient data. Those extra conditions are implemented in [the pipeline analysis](../pipeline/streaming/weighted_rhythm.py) and do not retroactively change the official rule.

NOAA-20 provides another raw VIIRS stream for a limited check. Its US Sunday index is 0.832, with interval 0.798-0.870, over 2018-2024. Nepal, Bangladesh and Egypt do not pass their pre-specified tests in that check. Its shorter period and related instrument prevent treating it as a direct replacement for the original streams. See [the NOAA-20 report](../reports/review/noaa20/NOAA20.md).

## Newly active cells

A follow-up counts a 0.25-degree cell when it has a detection on a local day and none on the preceding day, separately for each stream. This is a newly active cell, not a verified ignition. Cloud, detection limits or a missed overpass can make continuing activity appear new.

The follow-up applies the same weekday method. These results come from [the new-active-cell report](../reports/review/ignitions/IGNITIONS.md), whose historical filenames use "ignition". That filename does not establish an ignition observation.

| Country | Terra Sunday index | Aqua Sunday index | VIIRS Sunday index | Passing streams |
| --- | ---: | ---: | ---: | ---: |
| United States | 0.591 | 0.605 | 0.695 | 3/3 |
| Australia | 0.919 | 0.878 | 0.909 | 2/3 |
| Brazil | 0.827 | 0.869 | 0.803 | 3/3 |

Brazil now passes in VIIRS as well. Australia's Terra stream does not pass because Saturday is lower. India, Nepal, Bangladesh and Egypt still do not pass the country rule. The result suggests that repeat detections within active periods affect the raw-count weekday profile; it does not establish a cause for the newly active cells.

## Detection counts and FRP

The separate US daytime test compares the Sunday index in detection counts with the index in summed fire radiative power. Both measures use the same finite, nonnegative FRP records, with recorded zero retained. Its contrast is `delta = FRP Sunday index - count Sunday index`.

The primary common outage mask removes 73 dates; a second mask expands each frozen outage interval by a day at both ends and removes 87 dates. Eligible weekday denominators follow each mask. The numbers below are from [the FRP report](../reports/review/frp/FRP_TEST.md), for the primary mask over 2013-2024:

| Stream | Count index | FRP index | Delta | Adjusted interval for delta | Pass |
| --- | ---: | ---: | ---: | --- | --- |
| Terra | 0.627969 | 0.721653 | 0.093684 | -0.001657 to 0.204634 | No |
| Aqua | 0.644284 | 0.814539 | 0.170255 | 0.101864 to 0.243819 | Yes |
| VIIRS | 0.654520 | 0.745462 | 0.090942 | 0.045115 to 0.136984 | Yes |

The test uses 50,000 joint year-bootstrap draws. Bonferroni intervals have coverage `1 - 0.05/3`, or 98.333...%. To pass, a stream needs a delta of at least 0.05, an interval lower bound above zero, and positive leave-one-year-out and maximum-day-removal means under both masks. Aqua and VIIRS meet those conditions; Terra's interval crosses zero. The effect threshold is a project feasibility choice, not a NASA standard.

The local protocol was recorded before the original calculation. Its Git receipt was committed after the outcome was known. This is a pre-specified local test reproduced from preserved inputs, not a new prediction or an independently registered study. The [independent verification](../reports/review/frp/independent_verification.json) accompanies the report.

The Sunday deficit is stronger in counts than in sampled FRP for Aqua and VIIRS under these conditions. Summed FRP is sampled radiative power, not energy, emissions or burned area. Counts and FRP come from the same detections, so their difference does not establish a mechanism or ignition cause. The paired count indices also differ slightly from the original daytime results because the dates and inclusion rules differ.

## Controls and their failures

The official pooled static-source control is close to a flat weekly profile, with maximum absolute weekday deviations of 0.016 for Terra, 0.024 for Aqua and 0.017 for VIIRS. These are descriptive pooled checks in [the official gate](../reports/official/kill_test_gate.json). Pooling can hide a country-specific pattern, and industrial sources may themselves follow weekly schedules.

The later [year-level control review](../reports/review/controls/CONTROLS.md) separates source type and geography. US industrial sources show no passing Sunday dip in any stream. US volcanic detections do show a VIIRS-only dip: Sunday index 0.861, interval 0.749-0.956, raw p about 0.0011. Kilauea contributes 40,680 of the 42,920 VIIRS volcanic detections. Removing the 2018 eruption year raises the index to 0.891 and p to 0.0071, which no longer passes the corrected threshold. Removing the largest-count year does not remove the result. Aqua and the Alaska-only comparison do not pass.

That is an unexplained source-and-satellite-specific result. It prevents claiming the controls rule out every observation or processing artifact.

Brazil's Terra industrial control has Sunday index 0.913 over 2002-2024, with p about 0.0009. The effect is concentrated in 2002-2007; over the official 2013-2024 window its index is 0.966 and p is 0.15. Aqua and VIIRS industrial controls do not pass in either window. The longer-period failure explains why the stricter control-based decision differs from the original gate. The [control report](../reports/review/controls/CONTROLS.md) preserves both windows.

## What Nepal's non-result can detect

A power experiment starts from Nepal's real daily volumes. It shifts each year's weekday labels randomly, then plants a Saturday reduction by thinning detections. The official country rule is applied in 200 simulations per scenario. These are synthetic experiments on real volumes, not additional observed results. See [the power CSV](../reports/review/rhythm/b5_nepal_power.csv) and [method](../reference/rhythm_review.py).

| Planted Saturday reduction | Country passes | Terra passes | Aqua passes | VIIRS passes |
| --- | ---: | ---: | ---: | ---: |
| None | 0.5% | 0.5% | 0.5% | 0.5% |
| 10% | 0.0% | 2.0% | 2.0% | 13.5% |
| 20% | 12.0% | 6.0% | 7.0% | 84.5% |

The country rule often misses even the larger planted reduction because the MODIS streams have low detection power. A non-result therefore cannot establish no weekly pattern. The stronger VIIRS power is conditional on this simulation and does not by itself rule out a particular effect in the real record.

## The exploratory map

The map examines variation within countries after the national analysis. It uses 1-degree cells, with VIIRS as the map stream and Aqua as a comparison. A cell must average at least 300 detections per complete study year and have at least 8 usable years; each usable year needs at least 140 detections. These are the exact [published thresholds](../reports/official/rhythm_summary.json).

The mean-count eligibility calculation divides counts from archive-year-matched years by the full number of study years, including study years with no eligible cell records. A matched cell-year needs at least 95% of its records to match its archive year. The index itself then uses only the years meeting the per-year detection threshold. See [the map's eligibility code](../reference/rhythm_map.py).

The map uses 20,000 null draws and Benjamini-Hochberg correction at 5% across all tested cells of a stream. This differs from the national Bonferroni rule. A map significance flag means corrected `q < 0.05`; whether the tested day is also lowest is reported separately. See [the map implementation](../reference/rhythm_map.py).

The official VIIRS map tests 1,461 cells across the US, Australia, Brazil and India; 492 have significant dips. Neighbors share conditions and detections can cluster across boundaries, so those cells are not independent replications. Untested or gray areas have insufficient eligible evidence, not a demonstrated absence of a pattern. The [northeast review](../reports/review/NORTHEAST_INDIA_REVIEW.md) records the denominators.

India's national result does not pass, but its northeast contains a concentration of Sunday dips. After checking border geography, 14 of 21 tested northeast cells mostly inside India are significant, with median Sunday index 0.717. Another 5 cross-border cells have deeper dips, but less than half their land lies in India and their records contain only the Indian portion. Combining those groups without explanation exaggerates the mostly-inside result. See [the border analysis](../reports/review/NORTHEAST_INDIA_REVIEW.md).

The pattern is not uniform within the region. Of 4 cells at least 95% within Assam, 2 are significant and 2 are not. State assignments, boundaries and regional comparisons were examined after the national result. They remain exploratory and make no claim about who burns or why.

## The failed Bangladesh prediction

A follow-up prediction recorded before its analysis expected no significant Sunday dip in the Chittagong Hill Tracts. Two eligible cells met the recorded geographic fallback rule. One, at southwest corner 21 N, 92 E, had a VIIRS Sunday index of 0.490 with `q = 0.0004`; Aqua also showed a significant Sunday dip, index 0.564 and `q = 0.020`. The other cell's Sunday result did not pass. Its Friday index was 0.652 with `q = 0.011`. See [the preserved prediction and result](../reports/review/bangladesh_hills/RESULT.md).

The prediction failed. With only two eligible cells it is a limited geographic test, but the contradictory result remains part of the evidence. It does not change the national Bangladesh result or explain the regional pattern's cause.
