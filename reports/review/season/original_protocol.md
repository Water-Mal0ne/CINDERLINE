# FIRETRACE real-overlap sensor substitution feasibility protocol

Protocol fixed on 2026-11-14 before computing this endpoint. This is a retrospective stress test, not a new preregistered confirmatory study: 2020–2024 has already been inspected for other project endpoints. Two hours is the maximum initial investigation budget, not a requirement to spend idle time. No UI, production pipeline changes, model fitting, Git mutation, push or deployment is authorized by this experiment.

## Frozen scope

- Countries: Australia, Bangladesh, Brazil, Egypt, India, Nepal, United_States.
- Evaluation years: 2020, 2021, 2022, 2023, 2024, complete local calendar years; national `cell_id == ALL` only.
- Inputs: existing `outputs/firetrace/data/processed/harmonized_{country}.parquet`; model, selection, hashes and evaluation in `outputs/firetrace-merge-review/reports/`. Verify these agree with their main-checkout counterparts and the existing locked artifact hashes. Record full file hashes and repository HEADs before results.
- Reference: observed `raw_aqua`, a satellite reference, not actual fire/ignition truth. Preserve local dates as dates. Require every expected date exactly once, finite nonnegative required fields, and matching country/model/source identities. Missing or incomplete inputs are reported as exclusions, never silently zero-filled. Archive completeness does not establish clear-sky exposure.
- Frozen alternatives: `raw_viirs`; `B1 = raw_viirs * locked global ratio`; `selected = harmonized` from the previously selected country model. Do not generate or select a new M1. Where B1 is selected, selected and B1 must agree within numerical precision.

## Scenarios and outcomes

For each country/year, use Aqua before a cut date (exclusive) and the alternative on and after it. All eleven within-year first-of-month cuts February–December are the primary stress scenarios: 385 paired scenarios per alternative if all inputs are eligible. January 1 is a separate whole-year replacement control (35 per alternative). January 1 of the following year is a separate all-Aqua/no-handover control (35 per alternative). Do not pool controls with primary results. Expected scenario rows: 7 * 5 * 13 * 3 = 1,365.

Primary outcome: total variation distance of twelve monthly shares from continuous Aqua, `TV = 0.5 * sum(abs(monthly(candidate)/annual(candidate) - monthly(Aqua)/annual(Aqua)))`. This measures observed seasonal-distribution disagreement, not a fraction of real fires missed or moved. A zero reference or candidate annual total makes TV undefined; retain an explicit reason and do not label this perfect agreement.

Secondary outcomes: signed and absolute annual relative count error against Aqua; monthly absolute count error; reference and candidate maximum-month sets and their intersection (ties retained). These remain descriptive and do not replace the primary outcome. No new endpoint or chosen-country criterion may be substituted after seeing results without labeling it exploratory/additional.

Summaries: report the complete country/year/cut matrix. For primary scenarios give per-country mean and median TV for all three alternatives; paired selected-minus-raw and selected-minus-B1 differences; improved/tied/worsened counts using absolute tolerance 1e-12; annual relative errors; and each year's mean across its eleven cuts. Report equal-country macro summaries alongside the country table. Do not let high-count countries dominate an implicit weighted mean. Comparisons with the simple B1 baseline are mandatory. No p-values or confidence claims: cuts within a year reuse observations, countries share climate/measurement influences, and only five test years are available.

## Verification gates

1. Verify model/selection/evaluation hashes, source paths, Parquet metadata/manifest consistency, date completeness, country/model/source identity, finite/nonnegative values and unchanged input hashes after the run. Attempt exact-count reconciliation using the existing national-count dataset and frozen stratum ratios, without fitting anything; explicitly state if that independent source reconciliation is unavailable.
2. Identity substitution (Aqua for Aqua) and no-handover controls produce zero discrepancy within tolerance. Direct daily sums equal stitched and monthly sums; leap days are retained.
3. Whole-year positive B1 scaling leaves normalized monthly shape unchanged relative to raw VIIRS within tolerance. B1-selected countries reproduce selected values. A synthetic proportional pair corrects exactly; explicit missing, duplicate, negative and zero-total fixtures must not silently pass as valid observations.
4. A separate verifier must implement calculations independently, not import the runner, and reconcile all scenario outcomes. It must inspect the runner and assess whether its summary tells the full story.
5. A separate scientific reviewer must assess validity and the main-angle recommendation. Prefer predefined Nepal and Egypt as success/limitation probes but show all countries. Do not select favorable cut dates as representative; illustrative examples must be labeled and use a deterministic rule (nearest-to-median primary raw TV for that country, tie by year then cut month), plus January whole-year controls.

## Interpretation and stop rule

No minimum effect threshold is invented for this exploratory product-feasibility decision. Report actual effect sizes and consistency before making an explicitly qualitative recommendation. Distinguish: technical gate (valid, reproducible arithmetic); scientific gate (a bounded, interpretable reference comparison); and product gate (strong enough to lead a demo, a supporting diagnostic only, or stop).

Calibration need not win everywhere. A clear failure can support an honest calibration-limits experiment, but does not prove useful reconstruction. A dramatic raw-to-calibrated gain that B1 already achieves does not establish unique model skill. If gains are negligible, conclusions misleading, provenance unreconciled, or the only story requires cherry-picking, recommend supporting-feature status or stop. A main-angle recommendation must explain the new contribution beyond existing peak-week checks and a toy synthetic transition. Do not claim first-ever science, recovered true fires, forecast skill, or human ignition attribution.

All experiment scripts/results/reviews/figures live in `outputs/firetrace-feasibility`, outside both application checkouts. Neither original source data nor locked results may be overwritten. Append and label any protocol deviation; never silently edit this frozen document.
