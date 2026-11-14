# FIRETRACE limitations

## Interpretation

- A hotspot is a detected pixel, not an independent fire or ignition. One event can generate many detections across days, pixels and instruments.
- Aqua-equivalent counts are a calibrated instrument scale, not ground truth. Differences in resolution, overpass time, saturation and detection probability remain.
- An absent record does not distinguish a genuine absence of fire from obscuration or missed observations. Annual archive completeness is not observation completeness.
- A weekly dip is consistent with human scheduling. It cannot determine ignition cause, estimate the fraction of human-set fires, or distinguish prevention needs from forecasting needs on its own.
- The streams share underlying events and some measurement limitations. Agreement between them is not independent replication.

## Input coverage and spatial resolution

The current run's manifest determines supported countries and years. A seven-country configuration is not evidence that all seven were downloaded or evaluated. Missing files, incomplete years and unavailable control samples must produce explicit exclusions or `insufficient_data`.

Civil-time conversion depends on geographic timezone boundaries and the available timezone database. DST is applied through IANA rules; uncertain locations are not silently assigned solar time. Country boundaries and assigned rest days simplify substantial local variation.

Degree-based grid cells vary in area by latitude. Spatial density comparisons require area normalization beyond raw counts. Sampling, thinning, spatial subsetting and output-size reductions must be disclosed when used.

## Models

Calibration fitted in an overlap period may not transfer to different land-cover mixtures, climate conditions, fire regimes or satellite operation periods. A year bootstrap describes variability across available training years; it is not a complete prediction interval for every grid cell or fire season. Sparse strata can make finer models less reliable than the global ratio.

The test set must not be reused for tuning. A negative or inconclusive evaluation is a valid result and must not be hidden by selecting only favorable countries. No forced trend correction is justified. No 2000-present coverage claim is supported without actual early data and a validated instrument bridge.

## Rhythm statistics and controls

Year resampling preserves each year's aggregate weekday pattern but does not solve confounding, nonstationarity or observation bias. The random-weekday null assumes exchangeable weekday labels within each year. Short records and weak signals can be underpowered. Equal weighting across years describes the average year's normalized pattern, rather than the distribution of all detections pooled together.

Calendar exposure adjusts 52/53 weekday counts but does not measure clear-sky exposure. Inference remains conditional on that unmeasured factor. The displayed 95% intervals are pointwise, while the p-values use a fixed Bonferroni family. Daytime and control analyses are separate diagnostic families; they must not be searched for whichever result happens to look strongest.

Static industrial sources can follow human schedules, and volcanic detections may be scarce. These are imperfect controls. A nonsignificant control does not demonstrate absence of bias. Missing or flagged controls prevent an unqualified release verdict in the implemented gate.

Synthetic data can validate software under declared assumptions but cannot validate real-world generalization. A synthetic example must be visibly labeled in every exported figure, report and app view.

## Product use

The calendar describes historical observations. Critical periods are historical summaries, not operational fire forecasts. Anomaly flags are exploratory and should not be used as emergency alerts or stand-alone public-safety decisions. FIRETRACE is a hackathon research prototype; NASA does not endorse this project.
