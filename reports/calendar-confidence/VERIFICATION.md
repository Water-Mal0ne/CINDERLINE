# Verification receipt — 2026-11-15

Scope: the local `science/calendar-confidence` branch and its production build. **No push, merge into main or deployment was performed.**

## Automated checks

| Check | Result |
| --- | --- |
| Complete Python suite | 104 passed |
| Complete web suite | 153 passed |
| TypeScript and production build | Passed |
| Static output | 137 files; 65,734,368 bytes (62.689 MiB); index.html present |
| Largest file | globe.json, 12,999,487 bytes; no file above 25 MiB |
| Whitespace check | Passed |
| Original published science and data versus upstream | No modifications to existing pipeline, official reports or public data files |
| Latest upstream check | Fresh fetch still shows github/main at 5104f41, already an ancestor of this branch |

The build reports the existing large Three.js/globe chunk (about 576 kB before gzip). It remains lazy-loaded when Earth is opened. This warning does not fail the build.

Independent scientific verification:

- Annual corrections: independently reread 116 source partitions and matched all 5,756 corrections; 154 national and 1,848 detailed-cell annual comparisons reconcile within published daily rounding precision.
- Seasonal payload: independently matched 3,360 monthly values, 840 retained-month counts and 84 published summary metrics. The India better-total/worse-shape tradeoff and Nepal improved mean shape survive both masks. These are whole-year descriptive controls, not fresh validation or an assertion about every artificial handover.
- Reliability and upstream compatibility were reviewed by an agent separate from their integration. The seasonal panel and annual correction received separate independent reviews.

## Production-build browser checks

Served the built dist locally at `http://127.0.0.1:5182/`, using the in-app browser. Checked at 1440 × 1000 and 390 × 844, then reset the viewport override.

- All seven countries load a weekly calendar and matching national seasonal comparison.
- Seasonal individual-year / five-year-average controls, both outage masks, monthly shares / counts, and expandable exact-value table work.
- India and Nepal displayed metrics agree with the independently checked values; B1-selected countries show identical simple/selected conversions.
- Raw mode labels 2025 as raw VIIRS; a local selection shows that local accuracy is not established and does not present national errors as local errors.
- Weekly evidence opens and closes with its daily estimates and export controls.
- Custom-area radius selection around 27.7, 85.3 returns 12 Nepal cells and its own monthly calendar; the distinct outage/rounding policy is visible.
- 3D Earth renders on desktop and phone. The 2025 calendar correctly opens the 2024 globe with its explicit limit note.
- The aligned 2024 globe shows 344 of 366 calendar dates retained and 22 outage dates excluded.
- Earth/table navigation, daily-record filtering, cell inspection and drill-down work. The selected Nepal cell restores 2024-01-01 through 2024-12-31 in the daily calendar.
- The reading guide moves focus to the intended unusual-weeks section.
- Weekly Rhythm Index opens, and a fresh `?view=rhythm` navigation restores it on phone width; robustness, FRP and exploratory-map content remain.
- The frozen seasonal baseline is now labelled 2003–2024 while its 2025 date guide remains usable.
- No page-wide horizontal overflow on phone. The detailed seasonal chart/table scroll within their own containers.
- No new application-console errors after loading the production build.

Browser checks sample representative flows; they do not certify every browser, GPU, network condition or accessibility technology. The automated recovery tests cover malformed data, mismatched correction sources and retries that were not forced through the browser.

## Issues found and resolved during integration

1. A Windows case-insensitive filename collision resolved a lazy component import to its data helper. The helper is now `seasonComparisonData.ts`; TypeScript and the production runtime pass.
2. Local reliability wording incorrectly implied calibration of direct Aqua and raw values. It now distinguishes those cases.
3. The 2025 banner incorrectly called raw values converted. It now follows the selected display mode.
4. The historical seasonal caption inherited the extended calendar end year. A regression renders all seven country payloads to ensure the frozen 2003–2024 baseline stays separate from the date guide.
5. The five-year chart note described shares even in count mode. It now describes the active measure.
6. The globe recovery harness assumed a single fetch and only .ts imports. It now uses both actual resources, real source hashing and TSX resolution.
7. Generated payloads and verification receipts now preserve their exact bytes across Git checkouts, preventing Windows newline conversion from invalidating reproducibility checks.

Original source payloads, model coefficients, evaluation results, selection decisions and the existing Workers configuration are preserved. Scope limits remain documented beside the views and in the accompanying reports.
