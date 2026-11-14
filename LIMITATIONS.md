# FIRETRACE limitations

## Interpretation

- A hotspot is a detected pixel, not an independent fire or ignition. One event can generate many detections across days, pixels and instruments.
- Aqua-equivalent counts are a calibrated instrument scale, not ground truth. Differences in resolution, overpass time, saturation and detection probability remain.
- An absent record does not distinguish a genuine absence of fire from obscuration or missed observations. Annual archive completeness is not observation completeness.
- A weekly dip is consistent with people scheduling their burning. It cannot determine ignition cause, estimate the fraction of human-set fires, or distinguish prevention needs from forecasting needs on its own. Absence of a dip does not mean fires are weather-driven.
- The streams share underlying events and some measurement limitations. Agreement between them is not independent replication.

## Input coverage and spatial resolution

The release manifest verifies all seven configured countries: Australia, Bangladesh, Brazil, Egypt, India, Nepal and the United States. This is a regional collection, not worldwide coverage. Missing files, incomplete years and unavailable control samples must still produce explicit exclusions or `insufficient_data` in future builds.

The seven-country release uses 273 archives and 67,934,899 cleaned detections, with supported local years 2003–2024. It is a new fitted model scope, not the old two-country cache with extra labels. Adding training countries changes the global ratio and shrinkage target. The historical 76-archive Nepal/US release remains identifiable at commit `841998b`; its old metrics must not be presented as this revision's metrics. Cache reuse must retain the cache's own manifest rather than attaching a newer raw-directory manifest to older rows.

Civil-time conversion depends on geographic timezone boundaries and the available timezone database. DST is applied through IANA rules; uncertain locations are not silently assigned solar time. Country boundaries and assigned rest days simplify substantial local variation.

Degree-based grid cells vary in area by latitude. Spatial density comparisons require area normalization beyond raw counts. Sampling, thinning, spatial subsetting and output-size reductions must be disclosed when used.

The annual globe includes all 41,986 contributing vegetation-detection grid cells in the supported seven-country record. Daily drill-down remains limited to 12 training-selected cells per country, with cell files loaded on demand. An annual cell can therefore be inspected on the globe without having a daily drill-down view. The keyboard table shows the 20 highest-activity annual cells for the selected country/year; it is not a full-grid table. Neither view provides worldwide fire coverage or arbitrary-area analysis. Uncolored geography must not be interpreted as an absence of fire.

The globe uses one logarithmic color scale across all processed years and cells. This supports comparison across years, but compresses numerical differences; exact values should be inspected before drawing a quantitative conclusion. Geographic context is generalized Natural Earth/world-atlas data, not a precise boundary survey or a satellite coverage mask.

## Models

Calibration fitted in an overlap period may not transfer to different land-cover mixtures, climate conditions, fire regimes or satellite operation periods. A year bootstrap describes variability across available training years; it is not a complete prediction interval for every grid cell or fire season. Sparse strata can make finer models less reliable than the global ratio. The current selected model still has +51.68% monthly test bias in Egypt; mean peak-week error is 17.6 weeks there, 10.0 in the United States and 7.0 in India. Bangladesh's M1 validation advantage over B1 is small. These limitations remain visible alongside the favorable results. The completed 0.25°/0.5° selected-cell sensitivity diagnostic exposes much larger local errors than national metrics alone: US normalized monthly absolute error is 145.94% versus 144.35%, and Egypt 178.77% versus 145.25%, on 2018–2019. It reuses validation years, covers selected geography and is not independent ground-truth validation. Lower coarse-grid error can reflect cancellation and merging rather than better localization.

Observed Aqua is used directly for 2003–2012; converted VIIRS is used for 2013–2024. The early record is not a reconstructed Terra-to-Aqua estimate. Equal lower and upper conversion bounds in an observed-Aqua period mean no conversion was applied, not that the observation is certain. A separate Terra-bridge feasibility test fits 2003–2007 and validates 2008–2011. Count MAE improves, but timing is unchanged and ratio-only intervals contain observed Aqua in just 8.3–22.2% of active validation months. This does not qualify historical transfer or total reconstruction uncertainty. No pre-Aqua reconstruction is published, and this release does not support a 2000-present coverage claim.

The test set must not be reused for tuning. A negative or inconclusive evaluation is a valid result and must not be hidden by selecting only favorable countries. No forced trend correction is justified. No 2000-present coverage claim is supported without actual early data and a validated instrument bridge.

### Conversion stability and anomaly flags (review A2-A5)

- The VIIRS-to-Aqua detection ratio shows no trend distinguishable from zero in any country over 2013-2024 (year bootstrap; `reports/review/ratio_trend.csv`). But in the 2020-2024 test years the ratio is higher than in training for Egypt (+39%) and the United States (+10%). Aqua's orbit drifted to a later crossing in the early 2020s; these data cannot separate that drift from real changes in fire timing or size. The US weekly test correlation falls from 0.97 (2020) to 0.74 (2024).
- Bangladesh 2022 is a failed test year for the selected model (weekly bias +114%, correlation 0.18). Egypt is biased high in every test year (+36% to +66%).
- Converted VIIRS produces far fewer zero weeks than observed Aqua in Egypt (0.6% vs 9.4%). Low-activity anomaly flags before 2013 are therefore unreliable for Egypt (100 low flags in 2003-2012 vs 38 in 2013-2024). In all countries, anomaly flags near the 2013 switch partly reflect the conversion, and flags compare each week with all other years, so long-term trends also shift flags between the two periods.

- The MODIS `version` field in the FIRMS country files changes from `6.2` (2013-2017) to `6.03` (2018-2022) and `61.03` (2023-2024), crossing the training, validation and test windows. NASA describes Collection 6.1 as a calibration-only change, but we have not tested whether the version change shifts detection counts; it is a possible contributor to the test-year ratio differences above.
- The evidence-card interval is a bootstrap interval of the conversion ratio over training years, not a confidence interval for true detections.

## Rhythm statistics and controls

Year resampling preserves each year's aggregate weekday pattern but does not solve confounding, nonstationarity or observation bias. The random-weekday null assumes exchangeable weekday labels within each year. Short records and weak signals can be underpowered. Equal weighting across years describes the average year's normalized pattern, rather than the distribution of all detections pooled together.

Calendar exposure adjusts 52/53 weekday counts but does not measure clear-sky exposure. Inference remains conditional on that unmeasured factor. The displayed 95% intervals are pointwise, while the p-values use a fixed Bonferroni family. Daytime and control analyses are separate diagnostic families; they must not be searched for whichever result happens to look strongest.

Static industrial sources can follow human schedules, and volcanic detections may be scarce. These are imperfect controls. A nonsignificant control does not demonstrate absence of bias. In the official pre-specified test the control is pooled across countries; per-country matched controls are a robustness check, not part of the gate.

### What the rhythm result does and does not show

- The official decision (pass) comes from the pre-specified `kill_test.py` gate. All three passing countries rest on Sunday; Friday- and Saturday-rest countries did not show a dip, so this does not show the dip following each country's own rest day.
- Brazil's Terra industrial-source control dips on Sunday over 2002-2024, but the dip comes entirely from 2002-2007; over 2013-2024, the window fixed for the rest-day test, the control is flat. Brazil's Sunday dip is weaker on raw detections (VIIRS does not pass) but passes in all three satellites on new ignitions. Because of the 2002-2024 control, Brazil does not meet the stricter check (Terra index 0.913, adjusted p = 0.021); the official pre-specified result is unchanged (PASS). Year-level recheck: `reports/review/controls/CONTROLS.md`.
- A Sunday dip in industrial (type-2) static sources does not by itself mean a satellite artifact: some are industrial sites that may also follow the work week.
- US volcano detections show a Sunday dip in VIIRS only (0.861), almost entirely from Kilauea and sensitive to the 2018 eruption year; Aqua and Alaska's volcanoes show none, and the larger US industrial-source control is flat in all three satellites over 2002-2024. A processing or satellite artifact would be expected to appear across satellites and source types, so we treat this as an unexplained single-volcano, single-satellite result and report it rather than discount it. Year-level recheck: `reports/review/controls/CONTROLS.md`.
- Nepal cannot confirm or rule out a modest Saturday dip (review B5): with Nepal's real volume, a planted 20% dip passes the country rule only 12% of the time (VIIRS alone detects it 85% of the time); a 10% dip is almost never detected. "No dip in Nepal" means "no dip of 20% or more in VIIRS detections", not "no weekly pattern".
- Brazil's VIIRS stream does not have Sunday as its lowest day in 11 of 12 leave-one-year-out runs (review B2); Brazil passes on Terra and Aqua only.
- The official analysis uses 2013–2024 for all streams; the stricter release analysis uses 2002–2024 MODIS. The two can disagree, as Brazil's Terra control shows (its dip is confined to 2002-2007).
- Countries are treated as single units with one rest day; large countries mix regions with very different burning practices.
- The northeast India pattern is exploratory and its cause is unresolved. Five of the 26 northeast cells lie mostly outside India (their detections come from the Indian side of the border) and they carry the deepest dips; using only the 21 cells mostly inside India, 14 are significant (median Sunday index 0.717). Cells that are almost entirely Assam plains show a weaker, mixed dip (2 of 4 significant). Per-state p-values are not corrected for multiple comparisons. See `reports/review/NORTHEAST_INDIA_REVIEW.md`.
- The per-cell map is exploratory. Its thresholds (300 detections a year, 8 usable years) limit it to places with a lot of burning; grey areas mean too few detections, not "no dip". Neighbouring cells share weather and practice, so a cluster of significant cells is one regional pattern, not many independent findings. Area boundaries quoted for regional findings were drawn after viewing the maps.

Synthetic data can validate software under declared assumptions but cannot validate real-world generalization. A synthetic example must be visibly labeled in every exported figure, report and app view.

## Product use

The calendar describes historical observations. Critical periods are historical summaries, not operational fire forecasts. Anomaly flags are exploratory and should not be used as emergency alerts or stand-alone public-safety decisions. FIRETRACE is a hackathon research prototype; NASA does not endorse this project.

Seasonal statistics and anomalies exclude bin 53 and other incomplete seven-day bins. This avoids comparing one or two days with a full week, but leaves the final calendar days outside those weekly statistical summaries. Their observations can still appear in the calendar and daily exports. A seasonal summary needs at least three eligible years, and missing history must remain unavailable rather than be filled with invented values. National seasonality does not become cell-specific when a cell is selected. Exported dates place historical windows into a selected year for reference only.

Share links reopen the current published data and are not immutable evidence snapshots. A later model/data revision can change the values shown by the same link. The link preserves the selected daily series and evidence week, but not the Earth camera, annual-cell selection or Earth/table preference.
