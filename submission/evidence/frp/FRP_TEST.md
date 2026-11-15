# Count versus FRP: fixed US daytime comparison

**REAL FIRMS DATA, US daytime 2013-2024**

**Numerical verdict: PASS.** In US daytime observations from 2013-2024, the Sunday deficit was stronger in detection counts than in summed fire radiative power in MODIS Aqua and VIIRS S-NPP, under a pre-specified test.

## Chronology and scope

The local protocol was recorded before the original analysis. This Git receipt was committed after its results were known; this is not external preregistration or a new holdout.

Original local protocol: 2026-11-14T18:57:23.284Z; SHA-256 `1B88C8B3C7A1225FB2AA10E3B19DD9311CB7F4B022A9795C51552557BB434171`. The later Git receipt is `92626ed2f76fc6ab1bcefa6254d49609b7c6b982`. This run reproduces that completed analysis; it does not manufacture a new prediction. The original immutable receipt contains a historical local path; all new source manifests use relative paths, and that receipt JSON is not published to the website.

United States, local civil years 2013–2024, vegetation type 0, daytime. Terra, Aqua and S-NPP are separate. Only finite, nonnegative FRP enters both paired measures; a recorded zero is valid. Each yearly weekday total is divided by eligible weekday occurrences and normalized by the unweighted mean of seven weekday rates. Twelve annual Sunday differences are averaged equally.

## Results

| Mask | Stream | Count Sunday index | FRP Sunday index | Delta | Adjusted interval | Pass |
|---|---|---:|---:|---:|---|---|
| primary | Terra | 0.627969 | 0.721653 | 0.093684 | -0.001657 to 0.204634 | False |
| primary | Aqua | 0.644284 | 0.814539 | 0.170255 | 0.101864 to 0.243819 | True |
| primary | VIIRS | 0.654520 | 0.745462 | 0.090942 | 0.045115 to 0.136984 | True |
| padded | Terra | 0.628674 | 0.723932 | 0.095258 | -0.001334 to 0.208322 | False |
| padded | Aqua | 0.645867 | 0.819900 | 0.174032 | 0.105515 to 0.246464 | True |
| padded | VIIRS | 0.656298 | 0.749324 | 0.093026 | 0.046202 to 0.139520 | True |

Indices have baseline one; deltas are index units, not percentages of fires or emissions. Streams meeting every condition under both masks: Aqua, VIIRS. The table and accompanying sensitivity files show every stream, including failed criteria.

The same 50,000 joint year draws (PCG64 seed 20261115; int64) are used for every stream and mask. Two-sided Bonferroni percentile intervals use exact coverage 1 − 0.05/3 = 98.333…%. The point estimate must be at least 0.05 and the interval lower bound above zero, with positive leave-one-year-out and maximum-day-removal means. This is a specified annual-block model, not guaranteed uncertainty coverage from twelve real years.

## Input and official-count reconciliation

All 28 cache hashes, raw source hashes, completion records and archived daily counts/FRP sums are verified against the original snapshot. The historical aggregation-code signature is exact; its later promoted copy differs only in a descriptive report label. The unmasked clean counts agree exactly with the official daytime totals:

| Stream | Official count | Clean unmasked count | Difference |
|---|---:|---:|---:|
| Terra | 460657 | 460657 | 0 |
| Aqua | 631342 | 631342 | 0 |
| VIIRS | 2784451 | 2784451 | 0 |

The common primary mask excludes 73 dates; padding every frozen range by one day excludes 87. Primary support contains 3,804,061 detections and padded support 3,792,660. Every eligible FRP value is finite and nonnegative. All stream-years pass the ≥95% valid and ≤1-percentage-point weekday missingness-spread gates. Zeros and exclusions are listed separately. Eligible calendar dates are not measured clear-sky observation exposure.

## Independent checks

The separate checker recomputes observations, daily sums, indices, contrasts, inference and sensitivity from the clean caches without importing the runner. See [independent_verification.json](independent_verification.json) and its linked evidence; the receipt is required before the public payload is written.

## Limitations

- Summed FRP is sampled radiative power, not energy, emissions, burned area or fire counts.
- The same detections form both measures; a difference does not establish ignition cause.
- Twelve year blocks, correlated sensors and unmeasured cloud/overpass exposure limit inference.
- Terra does not meet the corrected uncertainty criterion; its interval includes zero.
- The effect threshold is a project feasibility choice, not a NASA standard.

This is a defensible additional measurement comparison, not proof of a new causal mechanism or a world-first result. It does not alter the official weekly-rhythm gate or the harmonization model.

## Reproduce

```sh
python -m pipeline.review.frp_test --data-root /path/to/original/firetrace
python scripts/verify_frp_test.py --data-root /path/to/original/firetrace --report-dir reports/review/frp
python scripts/plot_frp_test.py --report-dir reports/review/frp
python -m pipeline.review.frp_test --publish-only
```

The data root may also name its `data/processed/clean_cache_v2` directory. Raw archives and the saved aggregation tree are needed for provenance reconciliation. No download is performed. Use `--output` for a separate reproduction directory. `--publish-only` copies verified small artifacts into `web/public/evidence/frp` and creates `web/public/data/frp.json`; it does not deploy.

Source definition: [NASA FIRMS VIIRS attributes](https://firms.modaps.eosdis.nasa.gov/content/descriptions/FIRMS_VIIRS_Firehotspots.html). Full inputs, annual contrasts, all sensitivities and the unchanged original protocol accompany this report.
