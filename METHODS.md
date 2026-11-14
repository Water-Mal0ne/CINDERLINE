# FIRETRACE methods

FIRETRACE compares recorded fire detections on a named instrument scale. It does not estimate the true number of fires or classify ignition causes. Read the generated reports for the actual datasets, supported periods, selected model and measured results of a particular run.

## Data and provenance

The source is [NASA FIRMS country archives](https://firms.modaps.eosdis.nasa.gov/country/). Downloads record URLs, transfer status, annual archive bounds, row counts and hashes in a manifest. A complete download establishes the input file's scope; it does not establish that the satellite observed every cell on every day. Clouds and overpass gaps remain a separate limitation.

MODIS confidence below 30 and VIIRS low-confidence records are excluded. Terra, Aqua and VIIRS S-NPP retain separate stream identities. Type 0 forms the vegetation-detection analysis; types 1 and 2 remain available for diagnostic controls. Missing fire type is unknown rather than assumed vegetation. UTC acquisition times convert to IANA civil time before date, weekday or year assignment. Invalid timestamps, coordinates and unresolved timezones are excluded and counted. The primary spatial grid is 0.25 degrees. Grid cells are not equal-area units.

## Harmonization and evaluation

Aqua is the named reference scale. VIIRS-to-Aqua calibration compares a global-ratio baseline with a stratified-ratio candidate. The naive uncalibrated stream is a baseline, not evidence that a discontinuity must disappear. Training uses 2013–2017, model selection uses 2018–2019, and 2020–2024 is reserved for final evaluation. Results must identify unavailable periods rather than silently expanding a small sample into the full period.

The implemented B1 ratio is the training-period Aqua count divided by the VIIRS count across the supplied regions. M1 stratifies by region, day/night and reported FRP class: below 10, 10 to below 50, at least 50, or unknown. Each stratum shrinks toward B1 using a fixed 100-VIIRS-detection pseudo-count. These are empirical reported-FRP strata, not physically equivalent fire-energy bins across instruments. The per-country selected model minimizes validation daily MAE; ties retain B1. M2 is omitted. Calibration intervals use 200 whole-training-year bootstrap draws.

The exported map includes up to 12 cells per country chosen by training-period detection activity. National totals use all qualifying cells. This limited map is a prototype selection, not arbitrary global area coverage. The exported comparison prefers calibrated VIIRS values when available and otherwise uses Aqua observations. A numeric zero means no qualifying archived detections in the verified archive period; the separate coverage field still states that actual observing exposure is unknown.

The generated evaluation table reports bias, error, correlation and seasonal timing where the data support those metrics. A simple ratio is a valid selected model. Improved performance is a result to measure, not a success criterion to manufacture. Calibration uncertainty and actual observation coverage are different quantities; a bootstrap interval does not capture every source of uncertainty.

This build does not implement the pre-Aqua Terra bridge and therefore does not claim a 2000-present or reconstructed early record. Supported periods are those with verified Aqua/VIIRS archives and boundary coverage. Daily estimates are formed directly from daily stratified counts; monthly and weekly values aggregate those estimates. The exact selected model and any scope cuts are described in the generated harmonization summary and `DECISIONS.md`.

## Calendar

The calendar displays recorded or reference-scale activity, its sources and availability flags. Typical-season bands describe variation across historical years, not a forecast. Anomalies are relative to a stated historical comparison and do not constitute emergency warnings. Unknown coverage must remain distinguishable from zero recorded detections. Evidence cards and exports retain provenance and the chosen model.

## Weekly rhythm analysis

The hypothesis is motivated by [Earl, Simmonds and Tapper (2015)](https://doi.org/10.1002/2015GL066383). Rest days are fixed before inspecting results: Sunday for the United States, Australia, India and Brazil; Saturday for Nepal; Friday for Bangladesh and Egypt. These are analysis hypotheses, not a claim that everyone in a country follows one schedule.

The Python entry point is `pipeline.rhythm.run(detections, output_dir, label, manifest)`. It uses the cleaned local civil dates and never reconstructs them from longitude-based solar time. For each country and stream:

1. Exclude the configured current/future year (2026 by default) and years with fewer than 140 vegetation detections.
2. Verify complete input periods from the manifest. An explicit attested local calendar period is accepted. Otherwise require the canonical annual UTC archive and both neighboring UTC-year archives, conservatively handling local-date boundary spillover. This verifies input-period completeness only.
3. Divide each weekday's count by its number of occurrences in that calendar year, then divide those seven rates by their mean.
4. Average the yearly indices equally. Require at least five eligible years.
5. Resample whole years 2,000 times for pointwise 95% percentile intervals. Each country/stream/subset has a stable, separately seeded random generator.
6. Form 5,000 null draws, independently selecting a random weekday from each year's seven indices and averaging across years. The one-sided p-value includes a plus-one correction. This assumes weekday-label exchangeability under the null; it does not prove that every source of temporal confounding was eliminated.
7. Apply Bonferroni correction across the fixed 21 country × stream hypotheses. The available-data count does not shrink this family. Daytime-only estimates and diagnostic controls use separate fixed families and are labeled as sensitivity/diagnostic analyses.

A stream supports the predefined dip when the rest day has the lowest mean, its 95% interval upper endpoint is below 1, and its adjusted p-value is below 0.05. Estimates with insufficiently verified input periods may still appear in reports as exploratory, but cannot satisfy the release gate. Confidence intervals are pointwise; the multiple-comparison correction applies to p-values.

## Diagnostic controls and release gate

Types 1 and 2 are analyzed using the same per-country, per-stream annual exposure adjustment, resampling and null method. They are not pooled into one global weekday count. Industrial/static sources may themselves have weekly schedules, and volcano observations may be sparse. A detected control dip is therefore a diagnostic flag requiring investigation, not automatic proof that the vegetation result is wrong. A nonsignificant control is not evidence of equivalence and does not establish equal sensor coverage.

The statistical criterion requires the US replication check and at least two other countries, each supported by at least two streams. Matching control results must also be available and unflagged for the supporting streams. Missing controls can therefore prevent release even when the statistical criterion passes. The report separates `statistical_decision` from the overall `decision` and explains the reasons.

The overall decision is `pass`, `fail` or `insufficient_data`. Synthetic input can exercise the statistical criterion but can never set `production_allowed` to true. A failed US replication check calls for investigation of the sample, method and comparability; it is not by itself proof of a software bug. The remaining cloud/overpass caveat remains visible even if the gate passes.

## Reproducibility outputs

The current real-data run supports Nepal and the United States for 2013–2024. Validation selects M1 for Nepal and B1 for the US. On the 60 test months in 2020–2024, Nepal M1 MAE is 30.2043 versus B1 198.4293, with M1 bias −8.0848%. US B1 MAE is 1606.3004 versus M1 2078.6268. These quantify agreement with Aqua archived detections, not independent ground truth. The overall rhythm gate is `insufficient_data`: the US criterion passes in three streams, Nepal passes in none, and other configured countries have no evaluated data. No overall human-rhythm claim is enabled.

- `kill_test_results.csv`: all country/stream/subset estimates, control results, intervals and adjusted tests.
- `kill_test_gate.json`: statistical and release decisions with reasons.
- `kill_test_diagnostics.json`: sample exclusions, manifest status, settings and coverage caveats.
- `rhythm_results.json`: structured results consumed by integration.
- `rhythm.svg` and, when Matplotlib is available, `rhythm.png`: figures labeled with the input provenance.

Synthetic fixtures verify known signal recovery, null behavior, gate logic, period handling and reproducibility. They do not establish performance on real observations. The supplied original reference scripts remain in `reference/` for traceability; the executable implementation is in `pipeline/`.
