# Limitations and FAQ

CINDERLINE measures agreement between satellite records. Its reference is archived Aqua detections, not a complete account of burning on the ground. A detection is a sampled hotspot pixel; repeated observations of the same continuing event remain separate detections.

## Where the results need care

National agreement hides local and year-specific errors. Egypt's selected model has +51.7% weekly test bias, and Bangladesh's 2022 weekly comparison has +113.6% bias and correlation 0.180. In the United States, weekly correlation with Aqua falls from 0.968 in 2020 to 0.744 in 2024. The records cannot separate orbit drift, product changes and changes in the observed activity. [Sources: country evaluation](../reports/review/layer1_table.md) and [year-by-year review](../reports/review/HARMONIZATION_REVIEW.md).

Selected-cell checks are much weaker than national averages: US normalized monthly absolute error is 145.94% on the 0.25-degree grid and 144.35% after regrouping into 0.5-degree cells. These checks reuse validation years and selected areas; lower error after regrouping can come from cancelling opposing errors. A national calibration must not be presented as a validated local estimate. [Source: spatial sensitivity report.](../reports/scientific_validation/SCIENTIFIC_SENSITIVITY.md)

Known outages are excluded from the calendar, but the remaining dates do not establish cloud-free coverage. The displayed annual globe applies the calendar's supplier-specific exclusions, while weekly and monthly summaries omit affected whole bins. Custom-area data omit affected whole months and round cell-month values, so their sums need not match the annual globe. The frozen evaluation is a separate result and has not been replaced by the display correction. [Source: annual-calendar alignment report.](../reports/calendar-confidence/OUTAGE_ALIGNMENT.md)

Some apparent changes near the sensor switch can reflect measurement differences. Egypt, for example, has fewer zero weeks after conversion than in the Aqua record, affecting low-activity anomaly flags. The MODIS processing-version field also changes across the training and later evaluation windows; its effect on count agreement has not been isolated. [Sources: conversion and anomaly review](../reports/review/HARMONIZATION_REVIEW.md) and [recorded product versions](../METHODS.md).

The weekly-rhythm analysis uses each raw satellite stream separately. Its intervals account for variation between years, but weekday-specific cloud and observation exposure are not measured. The streams also observe overlapping activity, so agreement between them is supporting evidence rather than independent experiments. [Sources: method](../METHODS.md) and [interpretation limits](../LIMITATIONS.md).

A failed country rule does not prove that no weekly pattern exists. In the Nepal simulation, a planted 20% Saturday reduction passed the country rule in only 12% of runs. That measures the test's sensitivity under the simulation assumptions, not the probability that a real reduction exists. [Source: the simulation results.](../reports/review/rhythm/b5_nepal_power.csv)

The spatial rhythm map is exploratory. In northeast India, 14 of 21 tested cells mostly inside India are significant, while the deepest dips include cells crossing the border; each country's archive still supplies only that country's detections. A separate prediction of no Sunday dip in Bangladesh's Chittagong Hill Tracts failed in one of the two qualifying cells. Neither finding identifies a cause. [Sources: northeast India review](../reports/review/NORTHEAST_INDIA_REVIEW.md) and [the failed Bangladesh prediction](../reports/review/bangladesh_hills/RESULT.md).

Share links reopen the current published data; they do not freeze the data or model version. Historical seasonal windows and anomaly labels have not been validated as operational decision tools. [Source: product limits.](../LIMITATIONS.md)

## Questions from users and judges

### 1. Why not join the raw MODIS and VIIRS counts?

The instruments detect different amounts of activity because their resolution, sensitivity and observation times differ. In the US held-out weekly comparison, raw VIIRS is 601.4% above Aqua, while the selected conversion is 1.7% above Aqua. That improves comparability on Aqua's scale without establishing the true amount of burning. [Source: weekly evaluation.](../reports/review/layer1_table.md)

### 2. Why use converted VIIRS if Aqua was still observing?

The project tests continuity on Aqua's reference scale; the switch does not mean Aqua stopped observing. The published series begins converted VIIRS in 2013 because the local-year rule requires the corresponding UTC archive and neighboring years, making that the first eligible complete local year in this snapshot. Aqua remains the comparison record during the overlap. [Source: the historical-series method.](../METHODS.md)

### 3. Is this accurate enough or approved by NASA?

It is a tested research prototype, and NASA does not approve or endorse the conversion. On 2020-2024 weeks, Nepal's selected conversion has mean absolute error 11.3 Aqua-reference-equivalent detections per week, compared with 43.3 for the simple ratio; Egypt still has +51.7% bias. Suitability depends on the country, scale and task, and these results do not qualify the calendar for emergency decisions. [Sources: evaluation](../reports/review/layer1_table.md) and [product limits](../LIMITATIONS.md).

### 4. Does a better total mean the seasonal pattern is better too?

No: in India's retrospective common-date comparison, the selected model reduces mean annual count error from 13.83% to 4.05%, while monthly-share disagreement rises from 12.31 to 15.57 points. Those are the primary-mask results for the simple model versus the frozen selected model, using Aqua as the reference. They describe already-examined years, not a new holdout or a guarantee for every season. [Source: season-preservation report.](../reports/review/season/SEASON_CHECK.md)

### 5. What do zero, missing values and the uncertainty interval mean?

A raw count of zero means no qualifying archived detections; null means a field is unavailable, excluded or not computed. Small area-cell values can also round to zero, and neither zero nor null proves that no burning occurred. Converted daily intervals use 200 resamples of the training years and describe uncertainty in the fitted conversion, leaving cloud, sampling and day-to-day errors unquantified. An observed Aqua day has no conversion step, and daily intervals must not be added into a weekly confidence interval. [Sources: interval definition](../METHODS.md), [area rounding](../pipeline/area_cells.py) and [current display exclusions](../reports/calendar-confidence/OUTAGE_ALIGNMENT.md).

### 6. Can I inspect any area, and why are only some daily cells selectable?

The daily selector contains 12 cells per country chosen using training-period activity; national totals include all qualifying cells. The annual globe covers 41,986 occupied cells, and a separate custom-area tool combines monthly 0.25-degree cell values for a drawn rectangle or point-and-radius selection. Custom areas use national calibration, have unvalidated local accuracy, and currently cover 2003-2024. Their January 2013 reconciliation can differ because of missing preceding-UTC-year spillover in that build, with all reported national monthly differences below 0.6%. [Sources: daily and globe scope](../METHODS.md), [area tool](../reports/review/CUSTOM_AREA.md), and [area reconciliation](../reports/review/area/RECONCILIATION.md).

### 7. What changes for 2025, and can the calendar predict the next season?

The 2025 calendar uses the frozen conversion beyond the validation period and shows no calibration interval. Its continuity check is less favorable for several countries: converted VIIRS is 21.4% below Aqua in Brazil and 17.6% below in Nepal. The calendar and exported seasonal dates describe history, and neither predicts the next season nor supplies a risk score or warning. [Sources: 2025 continuity](../reports/review/extend2025/CONTINUITY.md) and [product limits](../LIMITATIONS.md).

### 8. Does the Sunday dip identify human-caused activity?

No, a weekday association cannot identify ignition cause or attribute individual detections to people. The official US Sunday indices are 0.723 for Terra, 0.667 for Aqua and 0.782 for VIIRS, with an average weekday normalized to 1. These are separate raw-stream results, not a pattern produced or discovered by harmonization. [Sources: official stream results](../reports/official/kill_test_results.csv) and [interpretation limits](../LIMITATIONS.md).

### 9. Was the weekly pattern already known, and what does this project add?

The project reproduces a known association described in the prior literature cited by its method. Its contribution is an inspectable historical calendar with reference comparisons, disclosed failures, season-preservation checks and a separate count-versus-FRP test. The official country rule passes the US and Australia in all three streams and Brazil in two; India, Nepal, Bangladesh and Egypt do not pass. [Sources: prior-work context](../METHODS.md), [official gate](../reports/official/kill_test_gate.json), [season check](../reports/review/season/SEASON_CHECK.md), and [FRP comparison](../reports/review/frp/FRP_TEST.md).

### 10. Do the controls rule out a measurement problem?

No, the controls are incomplete and sometimes disagree. Brazil's Terra industrial-source control dips over 2002-2024 because of its early years, although it is flat over the official 2013-2024 test window. US volcanic detections have a VIIRS-only Sunday dip, concentrated at Kilauea and sensitive to the eruption year, while the larger US industrial-source control is flat. The separate US daytime FRP comparison passes its fixed criteria for Aqua and S-NPP, but Terra's adjusted interval includes zero and fails. [Sources: control recheck](../reports/review/controls/CONTROLS.md) and [FRP results](../reports/review/frp/FRP_TEST.md).

### 11. Were the tests specified before the results were known?

The original rhythm rule was pre-specified, but US and Nepal data were already available and no Git record predates the first real-data analysis. The FRP protocol was saved locally before calculation, while its Git receipt was created after the outcome was known. The season-preservation work is retrospective. Those distinctions limit the claim: these are not externally registered prospective studies, and later checks must not be described as untouched tests. [Sources: decision chronology](../DECISIONS.md), [FRP protocol timing](../reports/review/frp/FRP_TEST.md), and [season-study limits](../reports/review/season/SEASON_CHECK.md).

### 12. What did AI do, and how can someone check the work?

Codex and Claude Code assisted with planning, analysis implementation, interface work, testing and documentation, and the team remains responsible for reviewing the claims. NASA FIRMS provides the observations; labelled synthetic fixtures test software and do not establish real-world accuracy. The [data and reproduction guide](05-data-and-reproduction.md) records the commands and source-cache limits, while the reports retain inputs, hashes and separate verification outputs. The full scope of assistance is in [AI_DISCLOSURE.md](../AI_DISCLOSURE.md).
