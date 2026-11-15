# Calendar confidence review branch

Branch: `science/calendar-confidence`. Review locally; **do not push, merge into main or deploy without the owner's approval**.

## Baseline and isolation

This branch combines GitHub main `5104f41` with the prior section polish `baf5a8c` at integration commit `347b0d1`. The original worktrees and branches remain intact, including `ui/qa-polish`, `ui-polish-v2`, `ui/section-polish` and the Workers migration. The uncommitted Workers configuration is untouched.

Main already contains the monthly calendar, custom area selection, 2025 extension, Weekly Rhythm Index, FRP comparison and the 2024 globe limit. These features are preserved. No new dataset was downloaded and no model was fitted or selected.

## Changes to review

- A national seasonal comparison separates count disagreement from monthly-share disagreement with Aqua. It uses the existing retrospective 2020–2024 study and common outage masks. It is not a fresh holdout or a forecast.
- Reliability details distinguish national evaluation from local accuracy, daily values from observation coverage, raw counts from converted values, and calibration intervals from prediction error.
- A collapsed reading guide links area selection, historical seasons, unusual weeks and evaluation.
- A source-bound correction layer makes annual globe values use the same excluded supplier dates as the published daily values. Original scientific files remain unchanged. The globe fails closed if the correction layer does not match its source.
- Nearby notes explain why annual daily sums can still differ from weekly or monthly calendar totals that omit whole outage-affected bins. Custom-area monthly values also use per-cell rounding.
- The 2025 banner now correctly names raw VIIRS when the raw baseline is selected.

Independent review found and corrected an overly broad local-calibration statement and the raw/converted 2025 label. No scientific values changed in those wording fixes.

## Scientific boundaries

Aqua is an observational reference, not ground truth. National agreement does not validate arbitrary local areas. The seasonal comparison shows a tradeoff: better count totals can coincide with worse monthly shape. Its two outage masks do not establish complete cloud-free observations.

The annual correction covers 2003–2024 and 5,756 cell-years. It removes the weighted contributions of 57,938 archived detections; that raw count is neither a count of distinct fires nor the converted deduction. Independent reconstruction reconciles 154 national country-years and 1,848 detailed-cell years within the expected daily rounding tolerance.

The 2025 extension is outside the existing 2020–2024 test. It is not added to the globe or custom-area data. Existing model coefficients, selection, evaluations and original published payloads are preserved.

## Verification and reproduction

Use an environment with the repository's Python dependencies installed, then run from the repository root:

```powershell
npm ci --prefix web
python -m pytest tests -q --basetemp work/calendar-confidence/review-temp -o cache_dir=work/calendar-confidence/review-cache
npm --prefix web test
npm run build
```

The final verification receipt records full-suite results and browser checks. The specialized scientific checks and provenance are documented in `OUTAGE_ALIGNMENT.md`, `SEASON_FEATURE.md`, `RELIABILITY_GUIDE.md` and `UPSTREAM_COMPATIBILITY.md` in this directory.

The generated website is portable. Rebuilding the annual correction from source requires the verified prepared partitions, which are local cache data rather than files needed to run the website. The outage report explains those inputs.

Before any later integration, fetch the `github` remote and compare the latest main with this branch. A clean merge today cannot guarantee no conflict with future changes. Review a PR before merging; this task does not authorize publishing one.
