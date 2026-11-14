# FIRETRACE limitations

## Interpretation

- A hotspot is a detected pixel, not an independent fire or ignition. One event can generate many detections across days, pixels and instruments.
- Aqua-equivalent counts are a calibrated instrument scale, not ground truth. Differences in resolution, overpass time, saturation and detection probability remain.
- An absent record does not distinguish a genuine absence of fire from obscuration or missed observations. Annual archive completeness is not observation completeness.
- A weekly dip is consistent with people scheduling their burning. It cannot determine ignition cause, estimate the fraction of human-set fires, or distinguish prevention needs from forecasting needs on its own. Absence of a dip does not mean fires are weather-driven.
- The streams share underlying events and some measurement limitations. Agreement between them is not independent replication.

## Input coverage and spatial resolution

The current run's manifest determines supported countries and years. A seven-country configuration is not evidence that all seven were downloaded or evaluated. Missing files, incomplete years and unavailable control samples must produce explicit exclusions or `insufficient_data`.

The harmonized calendar, globe and evaluation use the 76-archive Nepal/US snapshot with complete displayed local years 2003–2024. The human-rhythm analysis is separate: it uses seven countries' annual archives for 2013–2024 through `reference/kill_test.py`. The five extra countries are not part of the calendar, the fitted models or the globe. Cache reuse must retain the cache's own manifest rather than attaching a newer raw-directory manifest to older rows.

Civil-time conversion depends on geographic timezone boundaries and the available timezone database. DST is applied through IANA rules; uncertain locations are not silently assigned solar time. Country boundaries and assigned rest days simplify substantial local variation.

Degree-based grid cells vary in area by latitude. Spatial density comparisons require area normalization beyond raw counts. Sampling, thinning, spatial subsetting and output-size reductions must be disclosed when used.

The annual globe includes all 15,118 contributing vegetation-detection grid cells in the supported Nepal/US record. Daily drill-down remains limited to 12 training-selected cells per country, with cell files loaded on demand. An annual cell can therefore be inspected on the globe without having a daily drill-down view. Neither view provides worldwide fire coverage or arbitrary-area analysis. Uncolored geography must not be interpreted as an absence of fire.

The globe uses one logarithmic color scale across all processed years and cells. This supports comparison across years, but compresses numerical differences; exact values should be inspected before drawing a quantitative conclusion. Geographic context is generalized Natural Earth/world-atlas data, not a precise boundary survey or a satellite coverage mask.

## Models

Calibration fitted in an overlap period may not transfer to different land-cover mixtures, climate conditions, fire regimes or satellite operation periods. A year bootstrap describes variability across available training years; it is not a complete prediction interval for every grid cell or fire season. Sparse strata can make finer models less reliable than the global ratio.

Observed Aqua is used directly for 2003–2012; converted VIIRS is used for 2013–2024. The early record is not a reconstructed Terra-to-Aqua estimate. Equal lower and upper conversion bounds in an observed-Aqua period mean no conversion was applied, not that the observation is certain. No pre-Aqua bridge has been validated, and this release does not support a 2000-present coverage claim.

The test set must not be reused for tuning. A negative or inconclusive evaluation is a valid result and must not be hidden by selecting only favorable countries. No forced trend correction is justified. No 2000-present coverage claim is supported without actual early data and a validated instrument bridge.

## Rhythm statistics and controls

Year resampling preserves each year's aggregate weekday pattern but does not solve confounding, nonstationarity or observation bias. The random-weekday null assumes exchangeable weekday labels within each year. Short records and weak signals can be underpowered. Equal weighting across years describes the average year's normalized pattern, rather than the distribution of all detections pooled together.

Calendar exposure adjusts 52/53 weekday counts but does not measure clear-sky exposure. Inference remains conditional on that unmeasured factor. The displayed 95% intervals are pointwise, while the p-values use a fixed Bonferroni family. Daytime and control analyses are separate diagnostic families; they must not be searched for whichever result happens to look strongest.

Static industrial sources can follow human schedules, and volcanic detections may be scarce. These are imperfect controls. A nonsignificant control does not demonstrate absence of bias. In the official test the control is pooled across countries; per-country matched controls are a robustness check, not part of the gate.

### What the rhythm result does and does not show

- The official decision (pass) comes from the pre-registered `kill_test.py` gate. All three passing countries (United States, Australia, Brazil) rest on Sunday; Friday- and Saturday-rest countries did not show a dip, so this does not show the dip following each country's own rest day. A worldwide Sunday effect of non-human origin is made unlikely by the flat static-source control but is not ruled out by this test alone.
- Robustness checks: no passing country failed a robustness check. Under the stricter re-analysis (2014–2023 only), Australia and Brazil hold in 2 of 3 streams rather than 3, so their support is narrower than the United States'. Australia Terra (adjusted p 0.063) and Brazil VIIRS (adjusted p 0.084) do not reach significance under the strict rules.
- The official rhythm analysis uses 2013–2024 for all streams, so it differs from the 2003–2024 MODIS years shown in the calendar.
- Countries are treated as single units with one rest day; large countries mix regions with very different burning practices.
- The per-cell map is exploratory. Thresholds (300 detections a year, 8 usable years) limit it to places with a lot of burning; grey areas mean too few detections, not "no dip". Neighbouring cells share weather and practice, so a cluster of significant cells is one regional pattern, not many independent findings. Area boundaries quoted for regional findings were drawn after viewing the maps.

Synthetic data can validate software under declared assumptions but cannot validate real-world generalization. A synthetic example must be visibly labeled in every exported figure, report and app view.

## Product use

The calendar describes historical observations. Critical periods are historical summaries, not operational fire forecasts. Anomaly flags are exploratory and should not be used as emergency alerts or stand-alone public-safety decisions. FIRETRACE is a hackathon research prototype; NASA does not endorse this project.

Seasonal statistics and anomalies exclude bin 53 and other incomplete seven-day bins. This avoids comparing one or two days with a full week, but leaves the final calendar days outside those weekly statistical summaries. Their observations can still appear in the calendar and daily exports. A seasonal summary needs at least three eligible years, and missing history must remain unavailable rather than be filled with invented values. National seasonality does not become cell-specific when a cell is selected. Exported dates place historical windows into a selected year for reference only.
