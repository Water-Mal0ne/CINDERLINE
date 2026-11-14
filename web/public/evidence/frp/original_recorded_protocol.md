# FIRETRACE count versus observed radiative power: frozen feasibility protocol

Status: specified before computing or viewing new weekday-FRP contrasts. The accompanying `protocol.sha256.json` records the UTC freeze and SHA-256. This is a prospective specification of a new analysis of already-inspected historical records, not independent preregistration, a new holdout, NASA approval, or evidence of priority. The scientific question and thresholds were selected in the preceding research report. Do not edit this protocol after the freeze; any necessary deviation goes in a separate dated deviation log and prevents an unqualified protocol-pass claim.

## Question and bounded decision

Does the already-known US daytime Sunday detection deficit weaken when the SAME observations are weighted by their retrieved fire radiative power (FRP)? Predict a positive difference of at least 0.05 baseline-one index units between the FRP Sunday index and valid-FRP count Sunday index in at least two of Terra, Aqua and S-NPP VIIRS, with the uncertainty and robustness gates below.

This is a measurement comparison, not a causal test. The 0.05 effect threshold, 95% validity threshold and one-percentage-point missingness threshold are project feasibility choices, not established scientific or NASA standards. Twelve annual blocks are the effective resampling units. Satellite records are correlated and are corroborating streams, not three independent experiments.

Work starts 2026-11-14 18:54:26 UTC. The data/provenance gate is due within fifteen minutes (19:09:26 UTC). The final feasibility verdict is due within two hours (20:54:26 UTC). Fail or stop early on unresolved inputs; do not use a favorable provisional contrast to relax a gate. No UI, production cache, application source, branch, commit, push or deployment change is part of this test. All artifacts live outside the app repository under `outputs/firetrace-frp-feasibility/`.

## Fixed observations and provenance

- Country: United_States. Years: LOCAL civil dates 2013-01-01 through 2024-12-31 inclusive. Retain every eligible year, not a subset selected by the outcome.
- Streams: exact clean-cache labels `Terra`, `Aqua`, `VIIRS` (the latter must be shown by source metadata to mean Suomi-NPP, not a mixture with NOAA-20). Analyze separately; do not sum streams or calibrate FRP with count-harmonization ratios.
- Type: exactly `type == 0`. Time of observation: exactly `daynight == 'D'`. Existing clean-cache confidence filters must match `pipeline/clean.py`: MODIS confidence >=30; VIIRS nominal/high (`n`, `h`, `nominal`, `high`). Do not choose new FRP, confidence, geography or intensity thresholds.
- Data: existing `outputs/firetrace/data/processed/clean_cache_v2/*_United_States.parquet`; read the needed columns directly without calling a helper that writes/rebuilds caches. Read relevant UTC archive-year files including 2012 and 2025 boundary files, then filter by derived LOCAL date. A missing edge file is not automatically harmless: establish that it cannot omit eligible local observations or fail the completeness gate.
- Existing local-date/timezone conversion is the observation model. Check date, year and weekday consistency, stream/source mapping, absence of accidental duplicate file ingestion, and source identity. Retain existing source records rather than silently deduplicating observations by location/time. If actual duplicate source records are found and provenance cannot explain them, stop; do not invent a new deduplication rule.
- Inventory and SHA-256 the exact clean caches, count partitions, source manifests/completion metadata and relevant cleaning code. Reconcile ordinary counts by stream/local date (and source/archive-year where possible) against the corresponding `work/phase3/nepal-us/archives/United_States/{modis,viirs-snpp}/{file_year}/counts-*.parquet` and `done.json`. Sum partition counts; rows of aggregate Parquet are not detections. Check cached source identity against available raw archive/source SHA-256 records. A missing verifiable provenance chain or unexplained count mismatch fails the data gate.
- These are quality-filtered observations with eligible calendar dates, not verified daily clear-sky observation exposure. Do not interpret a calendar with no rows as proof of no fire. Archive/year availability establishes data support only; retain this limitation in the result.

## Fixed calendar masks

Use one COMMON eligible local-date calendar for all three streams in each primary analysis. Drop the UNION of the following inclusive ranges from every stream, even if a particular range affected only another stream. These are the exact ranges already used/documented in the repository; do not infer further outages from a desired US curve.

| Range, inclusive | Reason/source stream |
|---|---|
| 2020-08-16 to 2020-09-02 | Aqua documented science-data outage |
| 2022-03-31 to 2022-04-16 | Aqua documented safe mode |
| 2022-07-26 to 2022-08-10 | S-NPP safe mode/VIIRS return window used by project |
| 2024-07-09 to 2024-07-16 | S-NPP geolocation anomaly |
| 2024-07-24 to 2024-08-01 | S-NPP processing outage |
| 2024-05-31 to 2024-06-02 | Previously flagged all-seven-country S-NPP zero dates |
| 2024-11-04 to 2024-11-05 | Previously flagged all-seven-country S-NPP zero dates |

The primary mask treats these date strings as local calendar labels, explicitly acknowledging that source notices may use UTC and that product restoration can vary. The mandatory second mask expands EACH exclusion range by exactly one calendar day at both ends, takes the union, and intersects with 2013-2024. Preserve/export both exclusion-date lists and eligible days by year and weekday. An independently discovered additional documented outage is a protocol deviation requiring disclosure; it cannot silently replace these frozen masks. Neither mask certifies complete overpass/cloud coverage, and one-day padding does not solve every processing gap.

On each remaining eligible date, an absent observation row contributes zero *recorded detections* and zero *summed retrieved FRP*, while the date remains in the denominator. Excluded dates contribute neither numerator nor denominator. Record this zero-versus-unknown distinction. Never derive eligible days from dates with positive detections. There must be at least one eligible occurrence of every weekday in every year; every stream/year must contain positive valid-count and FRP weekday-rate averages, or the index is undefined and the headline fails.

## Data-validity gate, before effect calculation

FRP is valid exactly when numeric, finite and >=0. A reported zero is valid. Missing, negative, NaN or infinite values are invalid; do not substitute zero for those measurements in the paired estimand. First validate individual cleaned FRP values rather than trusting `frp_known`: the legacy aggregate counts non-null numeric values and could include invalid physical values.

For each stream/year, on the SAME vegetation/daytime and common eligible dates, compute total ordinary detections, valid-FRP detections, and invalid fractions. Require valid-FRP fraction >=0.95 and maximum minus minimum of the seven weekday invalid fractions <=0.01 (one percentage point) in EVERY stream/year, under BOTH masks. Each weekday's ordinary count denominator must be nonzero. Failure in any stream/year stops the new headline; do not retain only passing streams for a cleaner cohort. Report missing, negative, infinite and zero counts separately. Save numerical gate results without weekday FRP outcome contrasts until protocol freeze is recorded.

Require exact integer ordinary-count reconciliation. For legacy aggregate FRP comparisons, use a clearly documented floating-point tolerance only, not an effect-sized tolerance; if invalid FRP exists, reconcile ordinary counts and known-valid reconstructed subsets without pretending legacy sums are valid. Unresolved support, numeric, mapping, provenance or reconciliation problems at the fifteen-minute gate mean STOP/FAIL rather than more searching.

## Estimand and reproducible inference

For stream s, year y, eligible date d, define C(d) = ordinary quality-filtered count; V(d) = count restricted to individually valid FRP; and F(d) = sum of FRP over those V(d) observations. V and F always refer to the identical detections. Keep C for descriptive context; it is not interchangeable with V.

For weekday w (Monday=0,...,Sunday=6), E(y,w) is the number of eligible dates. For metric X in {C,V,F}, rate r(X,y,w) = sum of X(d) over weekday-w eligible dates / E(y,w). Normalize R(X,y,w) = r(X,y,w) / ((1/7) * sum over the seven weekday rates). This uses the UNWEIGHTED mean of weekday rates, not the pooled mean of all days, so 52-versus-53 occurrences do not change the baseline definition. Sum of the seven normalized indices must equal seven within floating-point precision.

Annual paired contrast: delta(s,y) = R(F,s,y,Sunday) - R(V,s,y,Sunday). Primary effect: arithmetic mean of the twelve annual paired contrasts, giving each year equal weight. Also report equal-year mean Sunday indices for C,V,F and all twelve annual contrasts. Do not normalize a pooled twelve-year series and call it this estimand. Display the complete seven-day profiles descriptively; only the three Sunday contrasts belong to the confirmatory family specified here.

Bootstrap: `numpy.random.Generator(numpy.random.PCG64(20261115))`, generate one array of 50,000 x 12 indices drawn uniformly from integers 0..11, corresponding to sorted years 2013..2024. Save/hash the draws or a compact sufficient reproducibility representation. Reuse EXACTLY the same draws jointly across streams, metrics and masks. For each replicate average the selected paired annual contrasts (sample years with replacement, preserving each year's joint metric/stream structure).

Use two-sided Bonferroni percentile intervals for the three primary stream contrasts: alpha_family=0.05; per-stream alpha=0.05/3; quantile probabilities 0.05/(2*3) and 1-0.05/(2*3), with NumPy's linear quantile method. Thus coverage is 98.333333...% per stream (normally displayed as 98.33%). This is a specified resampling interval under an annual-block model, not guaranteed frequentist coverage from twelve dependent real years; cloud, product and retrieval bias remain outside it. Do not replace percentile intervals after seeing results.

## Mandatory robustness calculations

1. Leave one year out: for each stream and mask, calculate twelve means from the remaining eleven annual contrasts. All must be strictly positive for that stream to pass. Report every omission, not only the most favorable.
2. Largest-day removal: separately for each stream/year/mask find the eligible date with maximum total F(d). Break exact ties by earliest ISO local date. Remove that ONE date from BOTH V and F (and descriptive C) AND their weekday eligible-day denominator. Recompute normalized annual contrasts and their equal-year mean. Require the resulting mean strictly positive for each passing stream under BOTH masks. Export selected dates and each maximum's fraction of that stream/year's total sampled FRP. This sensitivity intentionally has stream-specific removed dates; paired V/F support remains exact. Do not remove individual pixels, winsorize values, or choose a new cap.
3. Show primary and padded-mask results together. Do not select the better mask. All twelve study years are retained if they meet the data gate; no additional countries, nights, seasons or smaller geographic regions are tested as rescues.

## Frozen pass/fail and permitted interpretation

The complete data gate must pass in all three streams/years under both masks. At least the SAME TWO streams must each satisfy, under BOTH masks: mean delta >=0.05; the adjusted interval's lower bound >0; every leave-one-year-out mean >0; largest-day-removal mean >0. These are conjunctive criteria, not separate two-of-three votes. A failed numerical contrast is a scientific fail; an unresolved integrity/data gate is an inconclusive/blocked test, not evidence that the physical contrast is absent. Independent verification must reproduce eligibility, paired sums, estimates, intervals and gates before promotion. Report all three streams even when only two pass.

For wording that calls this a weaker Sunday *deficit*, additionally verify that the passing streams' mean valid-count Sunday index is <1 under both masks. FRP itself may be below, at or above 1: do not claim a smaller FRP deficit if no FRP deficit exists. General passing wording is: “In these US daytime records for 2013-2024, Sunday's relative activity index was higher when detections were weighted by their observed radiative power than when the same detections were counted, across [passing streams], under our fixed comparison.” If count<1 and FRP<1, “the Sunday deficit was smaller in sampled radiative power” is a defensible narrower description. If FRP>=1, state that explicitly rather than inventing a dip.

Fail wording: “This fixed comparison did not establish a stable count-versus-FRP Sunday difference meeting our feasibility criteria.” Integrity-stop wording: “The proposed comparison could not be validated within the feasibility gate; we do not present an FRP finding.” Neither means no effect exists.

Summed snapshot FRP is a sampled radiative-power signal (MW summed over observations), not time-integrated energy, emissions, smoke, burned area, severity, the number of fires, a direct measure of the intensity of each independent fire, a safe day for burning, or proof of who ignites fires. Summing within each observation stream avoids cross-satellite duplicate sampling but does not resolve within-stream persistence, geometry, cloud, retrieval/saturation or allocation issues. No new causal, religious or human-ignition claim is permitted.

## Sources and fixed reporting artifacts

Protocol derives from `outputs/FIRETRACE final scientific edge.md`, idea 1; `outputs/firetrace/pipeline/clean.py`; `pipeline/review/no_observation.py`; `reports/review/OUTAGES.md`; and prior `research_notes/FIRETRACE final scientific edge/science_validity.md` and `data_opportunities.md`. The final report should link those exact local artifacts and NASA's [VIIRS product description](https://firms.modaps.eosdis.nasa.gov/content/descriptions/FIRMS_VIIRS_Firehotspots.html) for interpretation. It must distinguish data availability, computational verification and scientific inference.

Save input/hash inventory, source reconciliation, exclusions/exposure, missingness table, daily C/V/F table, annual indices, complete contrasts and uncertainty, robustness tables, machine-readable verdict, independent verification and one short reader-facing verdict. A standalone scientific chart is allowed after validation; it is not a website/UI change. If the test fails, preserve every result and return to the previously completed season-preservation experiment only after its separate common-date coverage check; do not start an open-ended replacement search.
