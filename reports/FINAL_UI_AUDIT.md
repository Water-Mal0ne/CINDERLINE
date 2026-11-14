# Final frontend audit

Reviewed November 14, 2026 by a separate checking agent. Scope: App, Globe, ShareView, data decoding, monthly comparison, national seasonal context and anomaly controls. The initial review was read-only; the coordinator then authorized only the border-rendering fix described below. No scientific data were changed. The coordinator owns browser checks and the final publication decision.

## Material finding sent to the coordinator

**Resolve overlapping country records in the globe and identify the selected country.** The seven-country payload has 130 grid centers shared by two country records (260 records). `Globe.tsx` builds both as identical coplanar quadrilaterals and maps a raycast face directly to one country record. Consequently a border cell can render one country's color while selecting another country's record; the current selected-cell card also omits the selected country while the nearby source label names the active region.

One concrete 2024 example is 23.125° N, 92.375° E:

| Record | Annual Aqua-equivalent value |
| --- | ---: |
| Bangladesh:23.00:92.25 | 47.87922992068856 |
| India:23.00:92.25 | 257.1184197966479 |

Both records previously produced the same four positions at the same sphere radius. This was a display/picking issue; the scientific country totals still reconcile correctly.

The coordinator authorized a bounded current-cycle fix, now implemented in `Globe.tsx` and the pure `globeCells.ts` helper. Each center renders one original country record: the selected country takes priority, otherwise country/ID ordering is stable. Selection occurs before annual-value filtering, so a selected-country null stays uncolored and a recorded zero remains visible. No values are added, rounded or republished. A region change rebuilds heat geometry. The selected-grid card identifies its own country and source, and an explicit border note explains the display rule.

Four focused tests pass against the actual seven-country payload and fixtures: the exact Bangladesh/India example in both input orders; stable foreign-region fallback; unique rendered centers for all seven selected countries; and null/zero/unavailable-year behavior. TypeScript and the scoped diff check pass. Command: `node --test web/tests/globe-cells.mjs` from the repository root. Browser verification of the rebuilt result remains with the coordinator.

## Other inspected behavior

- National and selected-cell series use the same explicit dictionary decoder. Unknown encodings, duplicate columns, wrong-width rows and invalid dictionary indexes fail rather than silently coercing values. The independent scientific audit separately checks the actual decoder against every original record.
- Region and cell fetches check abort state before applying results. Sharing is disabled while a linked series or evidence week is unresolved; URLs allowlist country/cell IDs and validate dates. Missing daily data is not replaced with another cell's series.
- Evidence cards now show whole-region/cell identity and coordinates. The current source includes the nationally selected calibration limitation and restores body overflow and prior focus on close. Share-panel Escape handling stops propagation and restores its trigger.
- Calendar and monthly displays preserve unavailable values, show day counts and partial-month warnings, and avoid treating the early observed-Aqua identity as independent model skill. The raw/harmonized control's relationship to the Earth reference scale is explicit.
- National climatology remains explicitly national when a cell is selected. Regional anomalies are withheld for cell selections and partial weeks; sorting uses absolute z-score without calling that hazard severity.
- Earth rendering is demand driven, cancels work on disposal, suspends offscreen/hidden work and exposes a table fallback. This audit did not force a graphics-context loss or measure browser frame rate.

No other material functional or scientific-presentation blocker was identified in this bounded source review. That statement is not a guarantee of zero defects or a substitute for the coordinator's seven-country browser and download checks.
