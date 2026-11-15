# Section-by-section polish review — 15 November 2026

## Scope and delivery boundary

This is a local follow-up on `ui/section-polish`, based on `cf6e20be4f7bc413bb0e022babb9c65cc7df7b44` from `ui-polish-v2`. The original checkout and PR #7 are left intact for the collaborator's review. This round does not push, merge, deploy, change published datasets, or alter scientific calculations, numbers, wording, captions, or caveats. It does not modify the Workers migration worktree.

Unslop by Damir Sokolovsky (@heydamir), https://github.com/heydamir/unslop, was applied in polish mode under CC BY 4.0. The existing graphite palette, DM Sans / IBM Plex Mono typography, scientific encodings and section order remain. No images, fonts, dependencies or new scientific features were added.

## Direction

1. Product: follow satellite observations from a country calendar to their evidence and geographic context.
2. Character: calm, precise, candid about the record's limits.
3. Visual language: a graphite observation workspace with restrained controls.
4. Main visual moments: the calendar and actual Earth data, supported by real charts.
5. Signature: keep dates, coverage, scope and source context close to each value.

## Agents and cross-review

- Explore agent: comparison, calendar, seasonal context and anomalies.
- Evidence/Methods agent: validation table, evidence drawer, source links and sharing.
- Earth/Rhythm agent: globe framing, selected evidence and country-control scope.
- Integrator: shell/sidebar, browser checks, shared stylesheet integration and final verification.

After implementation, the Explore agent independently checked shell, Evidence/Methods/Share and preservation. The Evidence/Methods agent independently checked Explore and Earth/Rhythm. Browser testing caught two further issues: the sticky drawer header's uncovered top strip, and selected globe evidence being offscreen on phones. Both were corrected and checked again.

## Findings and changes by section

| Section | Finding | Result |
| --- | --- | --- |
| Masthead/navigation | The large introductory heading consumed too much of the initial working viewport. | Reduced masthead spacing and heading size; navigation and content unchanged. |
| Region/spatial controls | The optional grid preview competed with primary controls; static checkmarks beside observation sources looked interactive. | Native keyboard-operable Grid preview disclosure, closed initially. Scope/subset caveat remains outside and visible. Removed decorative map glow and static stream checks. Existing spatial selector remains available. |
| Calendar | Keyboard week exploration, outage styling, evidence links and scope controls already work. | Kept calendar behavior, scale colors and missing-observation handling. Corrected operational grammar from `1 years` to `1 year`. |
| Comparison | Pointer movement while swiping could change the inspected month. | Touch moves and pressed-pointer moves do not inspect a new month; intentional clicks/taps and unpressed mouse hover still do. |
| Seasonal context | The entire card could pan horizontally with its wide plot. | Only the plot scrolls; title, readout, slider, controls and caveats stay within the card. Keyboard selection remains available. |
| Unusual observations | Existing sorting, expansion, evidence links and empty states are sufficient. | Reviewed; no unnecessary rewrite. |
| Evidence drawer | The close control disappeared during long reads. | Sticky close header with a solid background and correct desktop/phone inset; no scrolled text leaks above it. |
| Sharing | Share details could stay open after the user moved elsewhere. | Outside pointer/focus dismissal, correct focus behavior, cancellation of stale clipboard completion, preserved fallback and Escape behavior. Close target is 44px. |
| Evidence & validation | Small colored model chips and numeric alignment made comparisons harder. | Neutral readable model labels, semantic row headers, right-aligned numeric columns and model-group separators. Values, precision, row order and scientific text unchanged. |
| Methods | Content structure was already clear; long source labels needed resilient wrapping. | Source-link wrapping, spacing and touch-target improvements. Process, limits and source wording unchanged. |
| Weekly Rhythm Index | Two independent country pickers could appear to control the same scope; wide tables lost country context. | Visible labels distinguish weekday charts from the exploratory map. Country column stays visible during horizontal table scrolling. Analyses and independent selections are unchanged. |
| Earth | Selected details stretched the stage; coverage obscured part of the globe; phone controls had awkward gaps. | Fixed-height canvas, instructions and coverage in their own rows, coherent year/legend groups, selected evidence below the stage. |
| Earth navigation | Global framing assumed a fixed distance, and phone canvas selection gave no visible route to details below the viewport. | Fit the sphere to the narrower field of view; preserve relative zoom on resize. A conditional Inspect selected cell shortcut focuses its evidence on request, without auto-scrolling during selection/orbiting. |

## Unslop passes

1. Spacing: compact masthead, consistent plot/readout spacing, stable Earth composition and grouped controls.
2. Color: retain data colors and restrained graphite chrome; remove decorative glow and neutralize model-chip decoration.
3. Icons: remove misleading static checks; retain functional icons and a disclosure indicator.
4. Copy: add only operational disclosure/picker/selection labels and singular-year grammar. Preserve scientific content exactly.
5. Type: make model rows and numbers readable; preserve fonts and data precision.
6. Layout: plot-only scrolling, stable canvas, selected evidence beneath Earth, responsive year/legend grouping.
7. Details: sticky close control, sharing dismissal/focus, native disclosure keyboard behavior, 44px close target.
8. Visuals: actual scientific plots and WebGL Earth remain the main visual material. No generated art or new assets.
9. Motion: retain existing reduced-motion behavior, lazy globe loading and demand rendering. Do not auto-jump when selecting/rotating Earth.

## Verification performed

### Automated and source checks

- Full integrated run before the final selection shortcut: **69 Python tests passed; 107 web tests plus the three prechecks passed; TypeScript and production build passed**.
- Final selection-shortcut suite: **7 focused globe tests passed**, including its additional behavior test. The full suite is rerun after the local commit; the final delivery receipt records that exact commit and outcome.
- New meaningful regressions cover comparison pointer behavior, outside share dismissal and stale copy completion, globe framing across aspect ratios, and explicit selected-cell navigation.
- Independent review compared against `cf6e20b`: published datasets and processing files are unchanged; scientific JSX text, numerical expressions/precision, caveats and result ordering are preserved.
- `git diff --check` passes. No dependency or lockfile changes.

### Browser checks

Production build served locally; tested at 1440×1000 desktop, 768×1024 tablet and 390×844 phone widths.

- All seven countries load their calendar and correct weekly evidence; no page-wide horizontal overflow at phone width.
- Grid disclosure opens/closes by keyboard; the subset/scope caveat stays visible.
- Share details dismiss on an outside click or moving keyboard focus outside.
- Drawer header stays at viewport top 0px while scrolled on desktop and phone; Close remains visible and usable.
- Seasonal End key selects week 52. The wide plot is contained by its own scroller; card/readout width stays within the viewport.
- Validation and Methods render at desktop/phone widths; source links remain readable.
- Weekly Rhythm Index opens, `view=rhythm` restores after reload, and the two labeled country pickers retain their independent scope.
- Real WebGL canvas renders at desktop 753×420, tablet 652×420 and phone 307×320. Global Earth fits the frame. Country focus works.
- Evidence → annual Earth → selected daily record retains the year and correct cell identifier.
- Phone canvas selection reveals Inspect selected cell. Activating it focuses the matching region and brings the evidence into view.
- Selected annual/daily outage-handling notice remains verbatim.
- No browser warning/error entries were observed during the final checks.

Local review evidence lives outside Git in `../firetrace-section-polish-review/`: `browser-checks.json`, `country-checks.json`, and screenshots for Explore, seasonal context, evidence, validation, Methods, Rhythm and Earth. This folder is not shipped in the web build.

### Final build size

Final code build: **119 files, 52,306,791 bytes (49.884 MiB)**. Largest file: `globe.json`, **12,999,487 bytes**, below the 25 MiB per-file limit. `dist/index.html` exists. There are only **122,009 bytes** remaining under the project's 50 MiB total budget.

The final post-commit validation result is recorded separately so it can name the tested commit without a self-referential commit-hash update.

## Known issues and limits

- The existing annual/daily outage-handling discrepancy remains disclosed, not fixed. The earlier audit found 31 affected cell-years among 1,848 published daily-cell/year comparisons. This round does not regenerate data.
- The existing year-control caption says “calendar below,” although the calendar precedes Earth. It was left unchanged because captions are protected by the user's instruction; approve a wording correction separately.
- The lazy Three.js/Globe chunk remains about 571 kB minified and triggers Vite's existing >500 kB advisory. It is still lazy-loaded; no new asset dependencies were added.
- Responsive widths and real WebGL were tested in the browser. Physical touchscreen gestures, screen-reader speech, every device/GPU and network interruption combination were not tested here. Pointer-handler regression tests cover the touch-selection fix.
- Actual evidence-file download contents were verified in the previous round; the unchanged export builder remains regression-tested. Downloads were not repeated in this round.
- This is UI and interaction QA, not independent scientific validation or a new hackathon-results claim. Good sections were retained instead of rewritten.

## Reproduce and collaborate safely

The local branch is `ui/section-polish`; it has not been published. The collaborator's existing PR #7 still refers to `ui-polish-v2` at the previous baseline. Do not treat this report as evidence that GitHub already contains the new changes.

From a checkout of this branch with Python test dependencies installed:

```powershell
npm ci --prefix web
python -m pytest tests -q --basetemp .test-temp/section-polish -o cache_dir=.test-cache/section-polish
npm --prefix web test
npm run build
```

Use a fresh writable temporary/cache directory for each Python run if Windows locks an older one. Review local changes and run the complete checks before any later publication. **Do not merge or deploy without the owner's instruction.**
