# Annual globe aligned to the daily calendar

Revision: `calendar-dates-v1`. This is a derived display layer, not a new fitted model or a replacement for the frozen scientific evaluation.

## What changed

The original annual globe summed all eligible archived detections, including detections on dates subsequently excluded from the daily calendar. A new, separately versioned correction file now removes those contributions from **every affected annual grid cell**. The original `globe.json`, national and daily-cell JSON, model ratios, model selection and official evaluation files remain unchanged.

The scope is the globe's existing **2003–2024** record. The later **2025 daily extension is not silently added to the globe**. Calculations use the already published supplier-specific exclusion dates: 16 dates in 2022 and 22 in 2024. Aqua outages after the 2013 supplier switch do not remove converted-VIIRS calendar values.

The generated file is 65,666 bytes. It subtracts contributions from **57,938 archived vegetation detections**, affecting **5,756 cell-years** across the full annual grid. These are detection records, not separate fires. The values subtracted are weighted Aqua-reference-equivalent contributions; 57,938 is the underlying raw count and must not be described as the converted deduction.

All-cell exact sufficient-statistic partitions were available. The 84 published detailed daily cells are independent reconciliation targets; they were not used as proxies for corrections elsewhere.

## Source and browser contract

- `pipeline/review/calendar_alignment.py` reads the declared pre-cleaned count partitions, the frozen model, the original annual globe and current published daily exclusions. It does not download, re-clean, refit or reselect anything.
- Source archive fingerprints must match the globe and model. Source hashes and every consumed partition hash are recorded in `alignment-build.json`.
- Local date and local year must agree; neighboring UTC archive years are included when resolving possible New Year spillovers.
- `web/public/data/calendar-alignment.json` stores an exact float dictionary and sparse `(cell index, dictionary index)` corrections grouped by year. It does not round corrections to displayed precision.
- `web/src/calendarAlignment.ts` independently verifies a portable SHA-256 identity over the original ordered cell IDs, year axis, archive fingerprint and IEEE-754 annual values. Changed or reordered data, duplicate or out-of-range corrections, impossible subtraction and repeat application fail closed.
- `applyCalendarAlignment` produces a new object and new cell-value arrays; the original loaded globe remains intact. Null annual observations remain null. A hypothetical entirely excluded year is unavailable, not zero.
- `annualCalendarCoverage` reports retained calendar dates and excluded dates for supported region/year pairs. These are **not counts of cloud-free or observed days**. Values are not extrapolated to a complete year.

## Independent verification

`scripts/verify_calendar_alignment.py` does not import the producer or its helpers. It separately reads all 116 declared source partitions relevant to the exclusion years, accumulates weighted contributions, compares the complete set of affected cell/year keys, and decodes the published daily tables itself.

The independent check passed:

| Check | Result |
| --- | ---: |
| Full-grid cell-year corrections independently matched | 5,756 |
| National country/year sums reconciled | 154 |
| Published detailed-cell/year sums reconciled | 1,848 |
| Largest absolute national discrepancy | 0.000165733 |
| Largest absolute detailed-cell discrepancy | 0.000704249 |
| Maximum allowed difference from 5-decimal daily rounding | 0.00183001 |

The tiny residuals are consistent with summing daily values published to five decimal places against the unrounded annual derivation. The supplied correction file is **not** patched to force exact agreement with rounded values.

Additional regression checks: **13 Python tests and 6 browser-module tests passed**. They include local-year boundaries, correct supplier and vegetation filtering, fixed ratios and sparse-stratum fallback, invalid source counts, null and zero preservation, full exclusion, stale source identity rejection, immutable originals, duplicate/out-of-range/excess corrections, actual Python/JavaScript digest agreement, and all 2,002 published annual/daily comparisons.

## Remaining scope differences

The newer custom-area monthly data intentionally omit **whole months** containing an excluded date and round each cell-month to tenths. They therefore do not have the same temporal support or precision as the daily-aligned annual globe. Their totals must not be promised to match. This work leaves those upstream data intact and supplies an explicit scope note for the parent UI integration.

The same applies to calendar summaries that include only complete weeks or complete months: sum of all retained daily values is a different quantity from sum of only complete bins. The annual view is labelled against **available daily values**.

Removing known excluded dates does not establish complete satellite coverage or eliminate clouds, overpass differences, residual processing gaps, calibration error or poor local accuracy. This change fixes an internal aggregation inconsistency; it is not fresh scientific validation or a forecast.

## Reproduce

From the repository root, with the original verified preparations accessible:

```powershell
python -m pipeline.review.calendar_alignment --preparations ../firetrace/work/phase3/nepal-us ../firetrace/work/phase3/bangladesh-egypt ../firetrace/work/phase3/australia-india-brazil
python scripts/verify_calendar_alignment.py --preparations ../firetrace/work/phase3/nepal-us ../firetrace/work/phase3/bangladesh-egypt ../firetrace/work/phase3/australia-india-brazil
python -m pytest tests/test_calendar_alignment.py -q --basetemp .test-temp/alignment -o cache_dir=.test-cache/alignment
node --test web/tests/calendar-alignment.mjs
```

The preparation paths are workspace examples, not dependencies on a particular person's absolute directory. Supply the equivalent verified preparation folders on another machine. The generated correction JSON and reports are portable; using the website requires no Python or local archive files.

## Bounded local-area feasibility

The fetched main branch already includes all-cell monthly custom-area exploration for 2003–2024. Therefore no separate hard-coded district prototype is needed. The cached date/cell/stratum sufficient statistics could support a later properly scoped daily regional study without new downloads, but national calibration still does not establish accuracy for an arbitrary local area. Any further local validation remains a separate experiment.

No branch was pushed, merged or deployed by this workstream.
