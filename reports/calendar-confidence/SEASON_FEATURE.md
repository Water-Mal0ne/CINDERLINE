# Seasonal comparison feature

The new Explore panel presents the independently verified retrospective season study already committed on `season-check`, now in main. It is not a new experiment, model fit or untouched test. It evaluates national whole-year replacement controls for 2020–2024, irrespective of the surrounding calendar's dates, raw/harmonized mode or cell selection. The 2025 extension is explicitly outside its scope.

The initial view shows equal-year mean monthly shares. A user can inspect each year, switch to monthly counts, and use either the primary common-date exclusions (73 dates over the study) or the one-day padded sensitivity (87 dates). Both remove identical dates from Aqua and all VIIRS alternatives. Raw VIIRS, B1, and the frozen selected conversion are compared against observed Aqua. The table separates absolute retained-total error from monthly-share total-variation disagreement (×100 points). Five-year errors are means of five yearly errors, not errors of pooled totals. Raw and B1 shares overlap for whole-year replacement, and the panel explains why.

`pipeline/review/season_payload.py` checks the preserved daily inputs, exclusions, whole-year summary and manifest against the passing independent verification receipt. It then accumulates monthly totals with `math.fsum`, rounds only the published monthly sums to nine decimal places, and verifies all 84 reported country/mask/alternative/error summaries. No locked scientific artifact is changed. The 42,544-byte payload records hashes and the numerical precision convention.

## Reproduction

From the repository root with the existing Python dependencies:

```powershell
python -m pipeline.review.season_payload --check
New-Item -ItemType Directory -Path .test-temp -Force
python -m pytest tests/test_season_payload.py -q --basetemp .test-temp/season-payload -o cache_dir=.test-cache/season-payload
node --test web/tests/season-comparison.mjs
```

Omit `--check` to rebuild only `web/public/data/season-comparison.json`. All source inputs are in `reports/review/season`; the receipt binds their bytes. The new panel is `SeasonComparison`, receiving `regionId`, `regionName`, and optional `cellId` from the parent. It aborts obsolete loads, validates payloads, presents retry on failure, and uses expandable semantic tables as a chart alternative.

## Design and limits

The design follows the existing graphite instrument interface. Product: historical national calibration comparison. Character: calm, exact, inspectable. World: scientific instruments. Main visual: four labelled monthly series. Signature: every plotted result can be read in a numeric table. No decorative images, gradients or motion were introduced. Controls use 44px minimum heights and focus rings; only the chart and tables scroll horizontally on phones. These choices follow the installed Unslop skill by Damir Sokolovsky (CC BY 4.0, https://heydamir.design/unslop).

Retained calendar dates are not measured clear-sky exposure. Missing dates are not extrapolated. Aqua is an observation reference rather than truth. Equal-year average curves may conceal year variation, so the year selector remains visible. The panel shows neither confidence scores nor claims about local precision, cause, hazard or forecasts. Full per-year scientific source and hash lineage remain available in the payload and original study.

Independent review and integrated browser/testing results are recorded by the coordinator; this file does not claim they have passed before they run.

## Implementation verification

- Payload generation passed all 84 reference-summary comparisons and produced 42,544 bytes. `--check` verifies byte-for-byte reproducibility.
- Six Python tests passed, including source-tampering rejection, missing/zero activity semantics, count-versus-shape invariants, and India/Nepal direction preservation under both masks.
- Five web tests passed, including every country/mask summary, all individual years, equal-year averaging instead of pooled-error cancellation, and rejection of unsupported 2025 or malformed data.
- TypeScript checking passed. The helper is deliberately named `seasonComparisonData.ts`: using the same basename as `SeasonComparison.tsx` with a different capital letter causes module-resolution collisions on Windows.
- A separate reviewer recalculated all 3,360 monthly series values and 840 month-support counts against the original study's independently accumulated monthly data; maximum sum-rounding difference was 4.99e-10. Its suggestion to distinguish share averaging from count averaging is incorporated.
- The chart scroll region is keyboard-focusable. Actual integrated browser checks remain the coordinator's responsibility.

## Frozen baseline caption correction

The coordinator's browser check found an upstream caption regression: `SeasonalContext` used the calendar's extended `meta.period_end` to label a climatology that was not recomputed. All seven current `weekly_climatology`, `critical_periods` and `anomalies` arrays match the pre-extension `baf5a8c` arrays exactly; `pipeline/extend_2025.py` and every published `extension_note` explicitly preserve the 2003–2024 seasonal baseline. The narrow correction labels the existing baseline as 2003–2024 while retaining the chosen date-guide year (including 2025). Scientific arrays are untouched. A regression renders the actual component for all seven extended country files and separately checks a cell/2015 date-guide view.
