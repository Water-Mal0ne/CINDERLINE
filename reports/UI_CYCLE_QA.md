# Local UI cycle verification

Date: November 14, 2026. Base: `fac0a00`. Branch: `ui/qa-polish`.
This cycle is local only. No GitHub push, Cloudflare deployment, or scientific regeneration was performed.

## Changes

- Empty, reversed and out-of-record dates keep the typed fields visible, show an accessible error, preserve the last valid URL and withhold dependent charts/exports until corrected. Full-record recovery is available.
- Calendar inspection shows exact bin dates, record counts and available-value counts. Partial-date totals are explicitly marked in the calendar and evidence drawer. Hover previews persist so the evidence action uses the inspected week.
- Missing daily-cell metadata produces a recoverable error. Evidence focus no longer resets on parent renders; navigation exposes its active page and footer scrolling respects reduced motion.
- The annual Earth table now reaches every available country record through pagination, coordinate search and a daily-record filter. Selection has an exact coordinate label and focuses its details. Annual-layer fetch errors expose a retry action; the year slider announces the year.
- Monthly CSV exports retain region ID/name and cell ID in their contents and use scoped filenames. Values, precision, day counts and null/zero distinctions are preserved.
- Seasonal weeks have a direct keyboard/touch slider. Mobile chart readouts, grid controls and pagination are more readable, including a narrow-screen pagination layout.

## Verification

- Independent read-only source review found no remaining blocker in this bounded diff. Its follow-up caught a mobile CSS precedence issue, corrected before the final build.
- `npm --prefix web test`: 40 named tests passed, plus existing data-contract, anomaly and demand-renderer suites. Ten new named cases cover date/week behavior, export provenance, exhaustive annual pagination, all 84 detailed-cell IDs and coordinate search.
- `.venv/Scripts/python.exe -m pytest tests -q`: 61 passed. Use the documented `tests` target; unscoped collection also finds an old ignored scratch module with a duplicate name in this workspace.
- `npm run build`: TypeScript and Vite passed. Final static bundle: 116 files, 51,990,560 bytes (49.5821 MiB), below the 50 MiB project budget. Largest file remains `globe.json`, 12,999,487 bytes. Vite still reports the existing >500 kB lazy Three.js chunk warning.
- All three `LOCKED_ARTIFACTS.json` SHA256 entries match. No pipeline, model, scientific validation or public data changes.

## Browser checks

Tested the local production build through the in-app browser, with desktop and 390px/320px viewport settings.

- Cleared End, reversed range and out-of-record dates: visible errors, disabled sharing, withheld dependent views and successful full-record recovery. Last valid URL stayed intact.
- Nepal table: page 2, daily-only filter (12 records), exact coordinate search, empty-state recovery controls and focused selected-cell details. Daily drill-down retains national-only seasonal/anomaly scope labels.
- United States table: page 2 of 744, year change to 2003 resets to page 1, actual-year accessible label, daily filter returns 12. Australia country change and southern-hemisphere coordinates also checked.
- Shared United States cell `40.75:-123.50`, October 2–4, 2020: Week 40 explicitly says 3 of 7 days. Downloading evidence keeps focus on the action and the dialog scroll lock intact.
- Actual downloaded monthly CSV identifies the country/cell and three available days. Its 9.57086 Aqua-equivalent total reconciles exactly within 1e-9 to the separately downloaded daily evidence.
- Seasonal slider Home/End reached weeks 1/52 with correct dated readouts. Final mobile monthly readout styles resolve to 11px labels, 16px values and 10px day counts.
- At 320px viewport, document content stayed within the 305px usable width; pagination content matched its 204px container without overflow. Wide tables scroll independently.
- Restored desktop Earth rendering and Australia focus. Final production session had no captured console errors. Local preview server and QA tab were closed afterward.

Screenshot: `../../FIRETRACE_local_ui_cycle.jpg` (local preview, not the published site).

## Limits

The fetch-retry and missing-cell-metadata paths were source-reviewed; unavailable networking/GPU conditions were not fault-injected in this browser pass. This is a bounded regression cycle, not a claim of zero possible defects. Calibration limitations and the disabled rhythm gate remain unchanged.
