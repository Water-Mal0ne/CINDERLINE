# FIRETRACE: Unslop design and full-flow review

15 November 2026. Baseline `3224721`, branch `ui-polish-v2`. No merge or deployment.

This pass uses [Unslop](https://github.com/heydamir/unslop), created by **Damir Sokolovsky (@heydamir)** and licensed under **CC BY 4.0**. The skill was installed in the user's Codex skills directory. This is an adaptation of its workflow to FIRETRACE, with scientific text and data protected by the user's instructions.

## Direction

- **Product:** Follow satellite fire records from a country calendar to the underlying observations.
- **Character:** Calm, exact, candid.
- **World:** An observation workspace with graphite instrument panels and a restrained ember accent.
- **Moments:** The real fire calendar and geographic Earth view; chart colors continue to identify their actual series.
- **Signature:** Dates, reference scale and coverage stay beside the observation being inspected.

The user explicitly requested implementation, so the skill's additional direction-approval pause was not needed. Three agents handled Explore/evidence styling, Earth/rhythm styling, and independent verification; the coordinator handled the shell and integration.

## Audit and nine passes

1. **Spacing:** The old sidebar and panels mixed 5/9/13/17px gaps. Normalize controls, sections and panels to a 4px rhythm while retaining necessary small chart-cell gaps.
2. **Color:** Blue/green surfaces, colored gradients and the hero wash competed with scientific charts. Use neutral graphite surfaces and quiet hairlines. Leave scientific series, heat scales and missing-value encoding unchanged.
3. **Icons:** Retain Lucide, align control icons at 16px with 1.5px strokes, and remove the purely decorative orbit/cross and redundant note icon.
4. **Copy:** Keep scientific wording, values, captions and caveats. Change only operational label casing and clarify export/drill-down actions. Existing uppercase scientific labels are retained as a deliberate exception.
5. **Type:** Retain DM Sans and IBM Plex Mono. Raise interface labels and explanatory text, use tabular figures and remove decorative italic emphasis. Chart labels remain tied to their actual SVG scale.
6. **Layout:** Keep page/section order and all four views. Use a 260px desktop sidebar and fluid content capped at 1504px; stack controls at narrower widths and retain horizontal scrollers for dense charts/tables.
7. **Details:** Use 8px controls, 12px panels, visible keyboard focus, and touch-sized actions. Keep dates/coverage close to values and preserve distinctions between loading, missing and zero.
8. **Visuals:** Remove the synthetic orbit. Real observations, the fire calendar and the interactive Earth provide the visual detail. No generated image or invented data was added.
9. **Motion:** Keep feedback restrained and honor reduced motion. Existing demand-driven Earth rendering and lazy loading remain intact.

## Full-flow changes retained in this pass

- Evidence drawers export a Markdown evidence brief with the selected dates, scope, exact daily values, sources, share link and existing caveats. CSV remains available under an explicit label.
- Evidence can open its year on Earth, closes the drawer and focuses the Earth panel. The action explicitly says annual.
- Earth drill-down retains the displayed year. Whole-region drill-down resets a previous cell selection, including when the country stays the same. Cross-country navigation preserves the chosen scale and year.
- Explicit date edits cancel stale shared-week hydration. Error/retry paths keep the intended year and focus the correct destination after recovery.

## Known data limitation and approved notice

An independent read-only audit found that all 84 published daily cells map to globe records and centers. However, 31 of 1,848 daily-cell/year pairs have annual globe sums that differ from available daily sums beyond rounding tolerance. The annual and daily products apply outage handling differently. This pre-existing discrepancy is **not repaired by this UI pass**.

The user approved this exact notice beside selected-cell drill-down:

> Annual globe totals and daily records use different outage handling and may not sum to the same value

No scientific data, calibration/model, official result or pipeline file is changed. The brief presents the selected daily records rather than substituting annual globe totals.

## Verification

- Independent web verification passed **101 tests plus three standalone prechecks**. The 15 new tests cover evidence-brief output, real App navigation/retry behavior and year-aware Globe callbacks. No mirror tests were added for CSS.
- A baseline-to-worktree AST audit found no unexpected scientific text, numeric constant or caveat removal. All 150 protected tracked files retain their content (118 raw-byte matches; 32 pre-existing LF/CRLF checkout differences). Seven calculation/selection/validation helpers are unchanged.
- The production preview was inspected at 1440px desktop, 768px tablet and 390px phone widths. All seven country calendars loaded 1,166 week controls and opened evidence bearing the selected country's name, with no alerts.
- A US 2024 daily-cell drill-down retained country, cell `41.50:-123.25`, January–December date bounds and focus on the calendar. Evidence-to-Earth closed the drawer, selected its year and focused Earth. The exact approved notice was visible with selected-cell actions.
- The real Markdown brief downloaded for Nepal, week 1 of both 2023 and 2024. Downloaded files were read and retained with the QA artifacts. The browser download handoff was slow; it is not included in claims about app performance.
- `view=rhythm` survived reload. The phone country detail and Daytime only controls worked. Methods' Data sources link focused its section. Dense phone tables/charts scroll within their containers; no document-wide overflow was observed. Tablet observation streams and guidance remain visible.
- Browser review corrected a legacy rule that kept validation numbers at 10px: they now render at 13px. It also corrected a fixed-height Earth canvas that left blank space beneath it: the canvas now follows the actual stage dimensions through the existing resize observer. The phone stage is 360px high.
- No browser console errors were recorded. Main, backup and Workers migration remain outside this change. The full Python/web tests, TypeScript and production build are run again after the commit; their exact receipt is stored with the external QA artifacts.

Screenshots and machine-readable receipts are retained outside the repository in `outputs/firetrace-flow-review/`; the source-preservation audit is in `work/unslop-review/`. Physical touch gestures and actual screen-reader speech were not tested. The existing lazy Globe bundle warning remains. Annual/daily outage reconciliation and scientific narrative changes remain separate work.
