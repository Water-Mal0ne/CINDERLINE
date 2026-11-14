# FIRETRACE methods

FIRETRACE compares recorded fire detections on a named instrument scale. It does not estimate the true number of fires or classify ignition causes. Read the generated reports for the actual datasets, supported periods, selected model and measured results of a particular run.

## Data and provenance

The source is [NASA FIRMS country archives](https://firms.modaps.eosdis.nasa.gov/country/). Downloads record URLs, transfer status, annual archive bounds, row counts and hashes in a manifest. A complete download establishes the input file's scope; it does not establish that the satellite observed every cell on every day. Clouds and overpass gaps remain a separate limitation.

The phase-2 analyzed snapshot contains 76 verified Nepal and United States archives: MODIS 2002–2025 and VIIRS S-NPP 2012–2025 for each country. It contains 10,142,672 cleaned records, including the retained diagnostic-control types. The complete local-year display covers 2003–2024. The manifest stored with the cleaned Parquet is the authoritative input snapshot when that cache is reused; additional downloads on disk are not automatically included in its provenance or results. The release manifest documents this 76-file snapshot, not every file now present in the raw-data folder.

MODIS confidence below 30 and VIIRS low-confidence records are excluded. Terra, Aqua and VIIRS S-NPP retain separate stream identities. Type 0 forms the vegetation-detection analysis; types 1 and 2 remain available for diagnostic controls. Missing fire type is unknown rather than assumed vegetation. UTC acquisition times convert to IANA civil time before date, weekday or year assignment. Invalid timestamps, coordinates and unresolved timezones are excluded and counted. The primary spatial grid is 0.25 degrees. Grid cells are not equal-area units.

## Harmonization and evaluation

Aqua is the named reference scale. VIIRS-to-Aqua calibration compares a global-ratio baseline with a stratified-ratio candidate. The naive uncalibrated stream is a baseline, not evidence that a discontinuity must disappear. Training uses 2013–2017, model selection uses 2018–2019, and 2020–2024 is reserved for final evaluation. Results must identify unavailable periods rather than silently expanding a small sample into the full period.

The implemented B1 ratio is the training-period Aqua count divided by the VIIRS count across the supplied regions. M1 stratifies by region, day/night and reported FRP class: below 10, 10 to below 50, at least 50, or unknown. Each stratum shrinks toward B1 using a fixed 100-VIIRS-detection pseudo-count. These are empirical reported-FRP strata, not physically equivalent fire-energy bins across instruments. The per-country selected model minimizes validation daily MAE; ties retain B1. M2 is omitted. Calibration intervals use 200 whole-training-year bootstrap draws.

The supported historical series uses observed Aqua detections for 2003–2012 and converted VIIRS detections for 2013–2024. A full local year requires the matching annual UTC archive plus both neighboring UTC archives. This conservative rule makes 2013 the first eligible VIIRS year in this snapshot, even though the instrument's records begin in 2012. The constructed raw comparison follows the same archive eligibility: raw Aqua before that transition, raw VIIRS afterwards. Source selection is based on availability rather than a forced 2012 discontinuity. Terra is retained as a separate stream and is never pooled into this reference series.

Daily cell exploration includes up to 12 cells per country selected by training-period detection activity. National totals use all qualifying cells. Detailed cell payloads are separate files loaded on demand, rather than embedded in the initial regional payload; this affects loading cost, not their numerical values. The annual 3D globe has a separate, broader spatial scope described below. A numeric zero means no qualifying archived detections in the verified archive period; the coverage field still states that actual observing exposure is unknown.

The generated evaluation table reports bias, error, correlation and seasonal timing where the data support those metrics. A simple ratio is a valid selected model. Improved performance is a result to measure, not a success criterion to manufacture. Calibration uncertainty and actual observation coverage are different quantities; a bootstrap interval does not capture every source of uncertainty.

This build does not implement the pre-Aqua Terra bridge and therefore does not claim a 2000-present or reconstructed early record. Supported periods are those with verified Aqua/VIIRS archives and boundary coverage. Daily estimates are formed directly from daily stratified counts; monthly and weekly values aggregate those estimates. The exact selected model and any scope cuts are described in the generated harmonization summary and `DECISIONS.md`.

For observed Aqua periods, the exported lower and upper conversion bounds equal the archived count because no calibration is applied. These identical bounds are not an estimate of perfect instrument accuracy or zero observational uncertainty. For converted VIIRS periods, bounds describe the training-year calibration bootstrap only.

## Annual 3D globe

The globe contains 15,118 occupied 0.25-degree cells contributing to the supported Nepal/US vegetation-detection series. These are all contributing cells, rather than the 12-per-country daily drill-down sample. Each cell is rendered at its actual grid center, derived from the grid's lower latitude/longitude plus 0.125 degrees.

Annual computation first groups qualifying detections by country, cell, local year, stream and the same reported-FRP/day-night strata used by harmonization. It applies the unchanged, validation-selected model and its existing ratios to eligible VIIRS counts; earlier eligible years use Aqua counts directly. Because these transformations are linear within strata, their annual cell totals equal sums of daily converted values, apart from floating-point rounding. The globe does not refit a model or use a different scientific scale.

Color uses a single maximum over every processed cell and year, with the transformation `log(1 + value) / log(1 + maximum)`. This fixed all-year scale prevents an annual rescaling from making a quiet year appear as intense as an active year. Zero recorded detections have a separate visual key; null values and unprocessed regions are not interpreted as no fire. Neither color nor cell area represents burned area or area-normalized fire density.

The Earth land and country outlines are geographic context from [Natural Earth](https://www.naturalearthdata.com/), redistributed by [world-atlas](https://github.com/topojson/world-atlas) 2.0.2. `scripts/prepare-map.mjs` converts its 1:110-million land and country TopoJSON into the bundled map assets. These generalized outlines do not define observation coverage or supply fire measurements; FIRMS supplies the detection data.

## Calendar

The calendar displays recorded or reference-scale activity, its sources and availability flags. Typical-season bands describe variation across historical years, not a forecast. Anomalies are relative to a stated historical comparison and do not constitute emergency warnings. Unknown coverage must remain distinguishable from zero recorded detections. Evidence cards and exports retain provenance and the chosen model.

Calendar bins are seven-day periods anchored on January 1, not ISO weeks. Seasonal summaries and anomaly comparisons use only bins 1–52 with seven distinct dates and seven available numerical values. The year-end bin 53 contains only one or two days and is excluded from those comparisons; other partial bins are also excluded. The calendar may still display the year-end observations without treating their short total as a comparable full week. Each seasonal percentile requires at least three eligible years. Anomalies compare a target year's complete bin with the same bin in other years, excluding the target year itself. Historical high-activity periods have positive median activity at or above the 75th percentile of available weekly medians.

The seasonal section remains a national summary when a daily grid cell is selected and labels that scope explicitly. Date windows are translated into the selected year for the display and calendar export; this does not turn the historical climatology into a forecast for that year.

## Weekly rhythm analysis

The hypothesis is motivated by [Earl, Simmonds and Tapper (2015)](https://doi.org/10.1002/2015GL066383). Rest days are fixed before inspecting results: Sunday for the United States, Australia, India and Brazil; Saturday for Nepal; Friday for Bangladesh and Egypt. These are analysis hypotheses, not a claim that everyone in a country follows one schedule.

**Official decision.** The published decision is the gate pre-registered in `reference/kill_test.py`, run on seven countries' archives for 2013–2024 (outputs in `reports/official/`): per complete year, weekday rate divided by the number of times that weekday occurs, normalised to a mean of 1; years averaged; 95% intervals from 2,000 whole-year bootstrap draws; one-sided null test from 5,000 draws of a random weekday per year; Bonferroni across all country × stream tests. A country passes when its predicted rest day is the lowest weekday and significant in at least two streams; the overall decision passes when the United States and at least two other countries pass. Static sources (types 1/2) are a pooled negative control.

**Robustness checks.** `pipeline.rhythm.run(detections, output_dir, label, manifest, official=...)` loads the official outputs and adds the stricter re-analysis below, reported next to the official decision and never replacing it. It uses the cleaned local civil dates and never reconstructs them from longitude-based solar time. For each country and stream:

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

In the robustness re-analysis, each officially passing country is checked for: rest-day upper bound below 1 in at least two streams; the strict criterion above in at least two streams; and at least two matched, unflagged per-country control streams. Failing a check is reported plainly in the app and in LIMITATIONS.md; it does not change the official decision.

The official decision is `pass`, `fail` or `insufficient_data`. Missing official outputs or synthetic input give `insufficient_data`; synthetic input can exercise the strict criterion but can never enable a real-data claim. A failed US replication check calls for investigation of the sample, method and comparability; it is not by itself proof of a software bug. The remaining cloud/overpass caveat remains visible even if the gate passes.

## Reproducibility outputs

The current real-data run supports Nepal and the United States for 2003–2024. The added early observations do not change the calibration, model-selection or held-out evaluation periods. Validation selects M1 for Nepal and B1 for the US. On the 60 test months in 2020–2024, Nepal M1 MAE is 30.2043 versus B1 198.4293, with M1 bias −8.0848%. US B1 MAE is 1606.3004 versus M1 2078.6268. These quantify agreement with Aqua archived detections, not independent ground truth. The official rhythm decision is `pass` (seven countries, 2013–2024): the United States passes in 3 of 3 streams, Australia in 3 of 3 and Brazil in 2 of 3; India, Nepal, Bangladesh and Egypt do not pass. All three passing countries rest on Sunday. All passing countries meet the three robustness checks; Australia and Brazil hold in 2 of 3 streams under the strict rules.

- `kill_test_results.csv`: all country/stream/subset estimates, control results, intervals and adjusted tests.
- `kill_test_gate.json`: statistical and release decisions with reasons.
- `kill_test_diagnostics.json`: sample exclusions, manifest status, settings and coverage caveats.
- `rhythm_results.json`: structured results consumed by integration.
- `rhythm.svg` and, when Matplotlib is available, `rhythm.png`: figures labeled with the input provenance.

Synthetic fixtures verify known signal recovery, null behavior, gate logic, period handling and reproducibility. They do not establish performance on real observations. The supplied original reference scripts remain in `reference/` for traceability; the executable implementation is in `pipeline/`.
