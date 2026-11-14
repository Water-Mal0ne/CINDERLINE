# FIRETRACE phase 2 QA

## Scope and verified checks

Independent source and data-contract checks; no browser session used. Final integrated Python suite: **39 passed in 4.52 seconds**. `npm --prefix web test` and `node web/tests/anomalies.mjs` both pass after all four landing sections were integrated.

The eight new cache/export test cases verify that content hashes and archive eligibility affect cache signatures; paths, transfer timestamps and file ordering do not; selected-country filtering isolates unrelated archives; and external cell files use portable names without colons. Decoding compact rows reproduces normalized source records, including null values and five-decimal export precision. These focused fixtures supplement the root's full payload checks without rerunning that large comparison.

The then-current 2013–2024 payloads each had 4,383 ordered, unique daily rows. JSON and CSV numeric fields matched within five-decimal serialization precision. Embedded evaluation values matched `harmonization_eval.csv`, and both payloads matched the report's `insufficient_data` rhythm decision.

## Reproduced defects sent to implementation owners

1. **Incomplete weeks can become false low anomalies.** One known day of 10 detections plus six missing days was compared with complete 70-detection weeks and labeled low. Incomplete reference weeks could conversely make a complete week appear high. Regression tests require complete comparable bins.
2. **Leap-year week 53 can create false high anomalies.** At a constant 10 detections/day, leap-year week 53 sums to 20, whereas non-leap week 53 sums to 10. The former was flagged high solely because its duration doubled. Regression requires no anomaly for this constant-rate fixture.
3. **Calendar normalization overwrote a valid raw baseline.** A 2012 observed-Aqua fallback of 12 was overwritten with missing VIIRS by a hard-coded switch year. Regression requires preserving the pipeline's declared raw value.
4. **Evidence-drawer scope mismatch.** The drawer looked up regional anomalies even for a selected grid-cell or truncated-week value. The integrated implementation restricts classification to complete regional weeks and explicitly labels other scopes.
5. **Cache provenance risk.** Reusing a cleaned cache while attaching an expanded raw manifest could qualify absent cache years as zero detections. Cache reuse now retains the cache's recorded manifest and warns when newly downloaded archives differ; analysis reuse checks its source signature. The historical-data owner explicitly merged the early observations into the cache for the present extension.

Four added calendar regressions initially failed, with two existing tests passing. After the root's fixes, all relevant calendar, harmonization and rhythm tests passed: **22 passed in 2.24 seconds**. The regenerated national series each contain 8,036 ordered, unique daily rows for 2003–2024. Early values are explicitly observed Aqua, including the 2012 raw fallback; 2013 onward raw values use VIIRS. JSON and CSV values match within serialization precision, and no week-53 anomaly is exported.

The complete evaluation CSV is exactly unchanged from the saved pre-extension baseline. Fitted ratios and model selections are also exactly unchanged. The rhythm gate remains `insufficient_data`.

## Verification limits

Optional direct HTTP asset checks were blocked by the local network sandbox (`WinError 10013`), not by a measured website failure. Public-site and browser checks remain with the root agent. No performance or statistical result was changed by this QA work.

## Expansion acquisition paused on user steering

The owned downloader was stopped after the user prioritized the 3D view. Staging remains at `work/additional-country-archives/manifest.json`; canonical files and the canonical manifest were not changed by this agent.

- 12 complete, CSV-validated and SHA-256-recorded Australia MODIS archives, 2001–2012.
- 3,313,218 raw rows; 263,988,648 bytes.
- No completed India or Brazil archives in this staging batch.
- No recorded failed archive; three interrupted `.part` transfers remain unqualified and must not be ingested.
- A future run of the canonical downloader can reuse the completed CSVs and restart incomplete transfers.

## Dependency audit

`npm audit --json` reported two vulnerable packages: Vite 5.4.14 (high aggregate severity) and its esbuild dependency (moderate). These concern development-server/tooling behavior; the audit does not demonstrate that static deployed assets are vulnerable in the same way.

The audit's suggested Vite 5.4.21 patch does not clear all reported advisory ranges, which extend through Vite 6.4.3. A bounded proposal is exact **Vite 6.4.4**, followed by the existing tests, TypeScript/build checks and another audit. Registry metadata confirms its Node requirement accepts the current Node 22.13, and `@vitejs/plugin-react` 4.3.4 permits Vite 6. Vite 6.4.4 depends on esbuild ^0.25.0. No forced fix, package edit or dependency installation was performed by this QA agent.

Representative advisory records: [Vite Windows launch-editor issue](https://github.com/advisories/GHSA-587h-7wmj-h5pm), [esbuild development-server issue](https://github.com/advisories/GHSA-67mh-4wv8-2f99).

The root subsequently upgraded to **Vite 6.4.6** and reported **0 audit vulnerabilities**. No global npm changes were requested or made by this QA agent.

## Anomaly panel and globe checks

Section 4 now has a dedicated `AnomalyPanel.tsx` with all/high/low filters, chronological or absolute-z sorting, missing-z handling, progressive loading and regional-scope messaging. `node web/tests/anomalies.mjs` verifies the actual pure selectors, including zero versus missing z-scores, both directions and nonmutation. TypeScript checking passed after the component was added. Browser interaction testing remains with the root.

All globe cell centers match their stored grid origins plus half the 0.25-degree cell size. Summed annual globe values match unrounded national harmonized totals for every 2003–2024 year: maximum absolute floating-point differences are 2.73e-12 for Nepal (252 cells) and 4.10e-9 for the US (14,866 cells). This check found no stream-pooling or cell-aggregation discrepancy.

A globe drill-down ID mismatch was found and corrected: globe IDs include a country prefix while daily-cell IDs do not. The integrated implementation strips the exact country prefix for lookup and callbacks. Source inspection also verifies the Earth texture's −π/2 alignment, a fixed all-year color maximum, and a surface-distance guard against selecting backside cells. Globe patches remain 0.25 degrees; the raycast maps each pair of triangles to its source cell. These renderer/picking corrections still require browser verification by the root.
