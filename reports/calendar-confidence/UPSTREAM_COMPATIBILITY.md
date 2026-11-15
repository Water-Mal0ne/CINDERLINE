# Upstream compatibility and annual-alignment review

Reviewed on 2026-11-15 by the reliability/guidance agent, independently of the parent integration and annual-alignment implementation. This review does not certify this agent's own reliability components. No commit, push, merge or deployment was performed by the reviewer.

## Compared revisions

- Published upstream: `github/main` at `5104f41`.
- Previous section polish: `ui/section-polish` at `baf5a8c`.
- Parent's integration checkpoint: `347b0d1` on `science/calendar-confidence`.
- New feature work was still being integrated in the working tree during this review. Runtime checks below include that work and the updated globe recovery harness.

## Compatibility result

No lost upstream feature or change to the published scientific inputs was found in the integration checkpoint.

| Area | Evidence | Result |
|---|---|---|
| Month-by-year calendar | `MonthCalendar.tsx` and `monthStats.ts` are identical to upstream; both calendar panels remain mounted from App. | Preserved |
| Arbitrary area selection | `AreaOfInterest.tsx` and `areaSelection.ts` are identical to upstream at the checkpoint. Bounding rectangles and radius selection retain the monthly grid data contract. | Preserved |
| 2025 national extension | Published data files are identical to upstream. App retains the beyond-validation note, no-refitting wording, missing calibration-interval explanation, and 2003–24 season/anomaly boundary. | Preserved |
| Globe ends in 2024 | The `GLOBE_LAST_YEAR` constant and date-restoration helper are unchanged; App clamps globe years and retains the explanatory note when the calendar includes later years. | Preserved |
| Weekly Rhythm Index | Routing helpers are identical to upstream; the rhythm view, robustness notes, exploratory cell map and independently scoped controls remain. | Preserved |
| FRP comparison | `FrpComparison.tsx` is identical to upstream and remains mounted for the US in the rhythm view. | Preserved |
| Earlier UI polish | Four section-polish CSS files, `globeViewport.ts`, `ComparisonChart.tsx`, `ShareView.tsx`, and `SeasonalContext.tsx` are identical to `baf5a8c`. App/Globe retain the collapsible grid preview, responsive fit, selected-cell shortcut and focus behavior. | Preserved |
| Calendar-first loading | App still opens the globe only after the user's action, through Suspense; the geographic layer does not replace the initial calendar. | Preserved |
| Published science | No checkpoint differences from upstream in `pipeline/`, locked model/evaluation/selection files, `reports/official/`, `web/public/data/`, Python tests or the build script. | Unchanged |

These comparisons distinguish unchanged published assets from the separate, additive annual-alignment file. The latter intentionally changes the derived displayed annual sums; it does not overwrite the published globe or daily data.

## Checks run by this reviewer

From `web/`:

```powershell
node --test tests/month-calendar.mjs tests/area-selection.mjs tests/frp-comparison.mjs tests/globe-last-year.mjs tests/rhythm-interaction.mjs tests/exploration-integration.mjs tests/explore-interactions.mjs tests/share-interactions.mjs tests/globe-viewport.mjs tests/globe-recovery.mjs
```

Result: **63 passed, 0 failed**. This covers restored rhythm state, monthly/area arithmetic, FRP handling, the globe year limit, selection/navigation, sharing and viewport calculations.

```powershell
node --test tests/globe-recovery.mjs tests/calendar-alignment.mjs
```

Result: **13 passed, 0 failed**. The alignment tests independently decode the actual published daily payloads and compare 154 national country-years and 1,848 published cell-years. The recovery suite executes the real alignment decoder and WebCrypto identity check. It checks malformed data, mismatched source identity, reloading both resources on retry, and the adjusted value reaching the grid table and selected evidence.

From the repository root:

```powershell
..\firetrace\.venv\Scripts\python.exe -B -m pytest tests/test_calendar_alignment.py tests/test_globe.py -q -p no:cacheprovider --basetemp reports/calendar-confidence/.pytest-tmp-independent
```

Result: **16 passed**. Source-stream filtering, vegetation-only counts, local-date year boundaries, frozen conversion and fallback ratios, excessive deductions, null/zero preservation and source identities are covered.

An initial current-tree run failed five recovery tests because the old harness only resolved `.ts` imports and fetched one resource. With explicit ownership from the parent, the reviewer updated only `web/tests/globe-recovery.mjs`: TSX imports now resolve, each resource has its own response sequence, real correction fixtures are remapped onto the small test globe, and the harness waits for asynchronous hashing. The failures are resolved; no application behavior was mocked out to make them pass.

These are targeted integration checks, not a claim that the final full build or browser rendering has passed. The parent owns final complete-suite and desktop/mobile browser verification after all agent files are integrated.

## Independent scientific review of annual alignment

Inspected `pipeline/review/calendar_alignment.py`, `web/src/calendarAlignment.ts`, `scripts/verify_calendar_alignment.py`, their tests, and the generated build/verification receipts. No scientific support or policy blocker was found for the current 2003–24 release.

- The excluded dates come from the existing national daily rows explicitly marked `no observation`, not from an assumption that zero counts mean missing coverage.
- The producer requires the same exclusion dates across all seven countries before using the compact shared coverage table. It does not silently generalize a different country's mask.
- Corrections use exact prepared local-date cell/stratum counts, filtered to vegetation and the source actually supplying each annual value. The 84 published daily cells are checks, not a sample used to estimate the other cells.
- Source archive identities, locked model identity and original globe values are bound to the output. Adjacent UTC archive years are included so local New Year boundaries are not dropped.
- The selected frozen B1/M1 factors and sparse-stratum fallback match the existing harmonization implementation. There is no new fitting, model selection or threshold.
- The frontend returns a derived copy and rejects incompatible source values. It preserves existing zero and null values, rejects negative/excess deductions, prevents a second application, and marks an entirely excluded year unavailable.
- Partial-year totals are not extrapolated. The note explicitly distinguishes retained calendar dates from clear-sky satellite observation coverage.
- Monthly area summaries retain their separate whole-month outage exclusion and per-cell rounding. The new note correctly avoids claiming that these AOI monthly totals necessarily equal a daily-aligned annual sum.

The build receipt records **5,756 corrected cell-years**, derived from **57,938 recorded detections** on excluded dates. Its separate verifier reaccumulates **116 declared source partitions** without importing the producer and reports PASS. Maximum absolute reconciliation differences are approximately **0.000166** nationally and **0.000704** for published cells, below the **0.00183001** daily-rounding tolerance. These differences are numerical reconciliation checks, not accuracy estimates against real fires.

## Isolation

All pre-existing worktree branch pointers remain at the supplied baseline: `ui-polish-v2` cf6e20b, `ui/section-polish` baf5a8c, `frp-test` cf2f4d3, `review/rhythm-ui-compatibility` 0557a2b, `season-check` 9ee15af, `story-wording` ff4a64e, `submission-final` 97113a5 and `deploy/workers-migration` fac0a00. Local `main` remains 290e756 and backup `ui/qa-polish` remains f8e7917.

Read-only status checks show the existing worktrees clean, except the Workers worktree's previously reported untracked `wrangler.jsonc`, which remains present. Only the new `science/calendar-confidence` worktree contains this cycle's work. The reviewer did not alter those other worktrees.
