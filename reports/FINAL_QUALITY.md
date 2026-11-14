# Final independent quality record

Date: November 14, 2026. Scope: the seven-country `seven-country-v1` release, its compact public data, the additive scientific validation, and the canonical reproduction package. No production code, data or scientific formulas were changed by this checking agent.

## Result

No remaining numerical, decoder or test failure was identified. The checks below passed against the integrated local source and public files. The coordinator owns the final production build, final static-size measurement, GitHub upload and any authorized deployment; this report does not assert those actions have completed.

| Check | Evidence |
|---|---|
| Full Python suite | 61 passed in 19.43 seconds |
| Web test suites | Passed: data contracts/exports, anomaly behavior, demand renderer and 26 share-state/integration tests |
| TypeScript | `tsc --noEmit` passed |
| Actual seven-country payload verifier | 5,119,422 numerical checks passed; 51,128,009 bytes in `web/public/data` |
| Browser codec | Actual `loadData.ts` exports exactly decoded all 91 tables / 731,276 records against original JSON |
| Scientific sensitivity | Independent recalculation matched 14 grid rows and 28 bridge rows across 266 metric comparisons |
| Credential-pattern scan | 257 tracked and unignored text files checked; no matching filenames; no secret values printed |

Earlier independent evidence in `PHASE3_AUDIT.md` covers exact baseline equivalence, all seven countries' national/annual counts, training-selected cells, 41,986 globe centers, 154 globe/national annual reconciliations, date boundaries and lossless encoding.

## Additive scientific validation

`pipeline/validation/science_checks.py` retains a fixed protocol and writes it before calculations. Its saved model hash matches the locked source model. Grid sensitivity selects twelve 0.5-degree footprints per country using only 2013–2017 vegetation counts. The 0.25-degree comparison uses the four children of each footprint, over exactly the same country-clipped geography and 2018–2019 dates. Model ratios and country choices are frozen. Independently recomputed training selections and all reported grid metrics match the saved results.

The report explicitly acknowledges that 2018–2019 also selected the original models; this is a sensitivity diagnostic, not untouched-test confirmation. Lower coarse-grid absolute error can result from cancellation and higher activity Jaccard from merging nearby detections. National invariance is expected for a linear country/stratum conversion. Those arithmetic properties are not presented as proof of true fire location or spatial robustness.

The Terra bridge fits country ratios on 2003–2007 and validates on 2008–2011. The independent recalculation recovered all fitted ratios, 200 whole-training-year bootstrap bounds, monthly/weekly error metrics and active-month interval inclusion rates. No 2020–2024 data enter either additional analysis. The saved narrative correctly distinguishes ratio calibration uncertainty from predictive or total reconstruction uncertainty and notes that positive scalar conversion cannot change Terra's peak timing. No pre-Aqua reconstruction is published.

The optional rhythm gate remains `insufficient_data`, with `production_allowed: false`. The raw and weighted paths use the same first-complete-instrument-year rule. Synthetic provenance remains unable to enable a real-data claim. No threshold was relaxed.

## Reproduction and browser scope

The canonical reproduction command and its tests were included in the full passing suite. Source review confirms a fresh output directory, guarded archive acquisition, reuse of locked evaluation when requested, separate sensitivity output, an isolated frontend build, and no automatic production deployment. Its orchestration was tested with controlled fixtures. A fresh multi-gigabyte network download and complete end-to-end reproduction were not rerun during this final check; the existing source/count/model equivalence evidence remains the basis for the release.

The coordinator reports successful seven-country browser checks for national views and raw/harmonized controls, and an exported seven-row evidence CSV checked against source values. Earlier coordinator checks covered Earth interaction, share-link restoration, mobile sharing and focus recovery. These are coordinator observations; the independent agent's frontend evidence is the complete decoder equality check, automated suites and source review.

## Publication bookkeeping

The dictionary candidate's earlier projected site size was 51,973,329 bytes, leaving 455,471 bytes under the 50 MiB budget. The actual final build must enforce the total-site and individual-file limits after the final UI edits. The largest data file is the 12,999,487-byte globe JSON.

At audit time, `reports/build_summary.json` still contained the candidate's 50,613,315-byte compact-data figure, excluding shared map assets. The verifier measured 51,128,009 bytes in the actual public data directory. The coordinator was notified to refresh this metadata with final build measurements; this discrepancy does not change any scientific value.

Independent recalculation and scan evidence are saved under `work/phase3-audit/sensitivity_checks.json`, `browser_codec_checks.json` and `final_secret_scan.json`. The credential check used common private-key, GitHub/AWS token and quoted credential-assignment patterns. It is a bounded scan, not a guarantee against every possible secret format.

## Final coordinator checkpoint

The final build passed at 51,977,020 bytes (49.57 MiB); build_summary.json now records actual data and build sizes. All 30 named web cases plus the data-contract, anomaly and renderer suites passed. The border-rendering issue from FINAL_UI_AUDIT.md was fixed and its four regression checks passed. Rebuilt browser checks confirmed the selected country/source, the cell calibration note and dialog scrolling; see BROWSER_QA_PHASE3.md. The implementation hashes and locked artifact seals were refreshed without changing fitted choices or scientific results. A preserved model_snapshot.json matches the sensitivity protocol hash. This cycle stops after commit and push; Cloudflare remains on the earlier verified two-country deployment.
