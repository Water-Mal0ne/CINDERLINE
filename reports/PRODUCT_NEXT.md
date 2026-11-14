# FIRETRACE next product improvements

Prepared during the phase-2 release freeze. Current production scope remains governed by the tested build; the following work does not claim unimplemented capabilities.

## Completed isolated prototype: share a reproducible view

The first addition lets a teammate or judge reopen the same country, date range, daily cell, scale, annual globe selection and evidence week. It directly supports FIRETRACE's claim that a chart can be followed back to its evidence.

Implementation lives in `work/phase3/product/explorationState.ts`, with integration notes and 18 passing Node tests. Strict TypeScript checking passes. Production files and dependencies were not modified.

The parser validates real civil dates, available archive boundaries, region-specific daily cells and exact published globe IDs. Invalid or stale settings recover with explanatory notices. It detects a changed dataset version when one is supplied. It keeps the globe year consistent with the current app's calendar end year. It neither embeds result values nor promises an immutable scientific snapshot.

## Ranked additions

| Priority | Addition | User value and evidence | Bounded implementation | Acceptance evidence |
| --- | --- | --- | --- | --- |
| 1 | Shareable evidence links | A judge or teammate can inspect the same dates and source observations after the demonstration. Current App selections live only in React state, so a reload loses them. | Integrate the completed pure URL-state helper, a share control, restoration notices and controlled globe selection. Keep only published identifiers in URLs. | Fresh-tab restoration, invalid-link recovery, Back/Forward behavior, delayed-fetch race check, clipboard fallback and data-release notice. |
| 2 | A sensor-comparison lens on the globe | The spatial view should make the central instrument-comparison problem inspectable, beyond displaying attractive annual heat. Current globe values are harmonized annual totals while the comparison chart carries the reference observations. | Add separately computed annual raw-Aqua and raw-VIIRS arrays for the same grid, plus a named-reference comparison mode. Keep separate legends, matched dates and source labels; use side-by-side views or an explicit scale toggle. Never present raw-detection differences as an environmental change or ignition cause. | Sums match the separate source streams; reference-scale error summaries use common eligible years; the user can identify the active instrument and units in every mode; no invented global coverage. |
| 3 | A coverage and provenance inspector | More countries are useful only when users can see whether their record is comparable. An archive download is not evidence of cloud-free observation coverage. Current sidebar lists instruments but does not visualize their supported date spans. | Add a compact country-by-stream timeline of archive-qualified years with a source status for each interval and a link to the manifest. Expose observed Aqua versus converted VIIRS and label unknown observational coverage. Reuse existing manifest and eligibility outputs. | Timeline years agree with the pipeline, unavailable years remain distinct from zero detections, cached/staged archives are distinguished, and mobile keyboard navigation reaches each interval. |

## What makes these stronger than a larger feature count

Each addition strengthens the same defensible story: an instrument change can alter the record, FIRETRACE exposes the comparison, and a user can inspect the supporting observations and limitations. Expanded country coverage should be published only after the same fixed training/validation rules, source checks and release gate have run. A failed optional weekly-rhythm gate remains a reported result; it is not a reason to change the criterion.

## Required handoff

The parent owns integration and publication. Pure-parser tests have passed; browser restoration and link sharing have not yet been implemented or tested. No prediction, causal classification, unvalidated historical reconstruction, or global data coverage was added by this task.
