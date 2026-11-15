# Independent observation-detail review

Status: **independent data and source-code review passed** for the 2024 observation layer. Browser interaction, full-suite and production-build verification are separate integration checks performed by the parent agent; this report does not claim they were performed by this reviewer. No merge, push or deployment was performed by this reviewer.

Scope: seven countries, VIIRS S-NPP standard archive observations acquired in UTC year 2024. The existing harmonized historical overview remains a separate measurement and dataset.

## Scientific acceptance criteria

- Use original detection coordinates, never distribute a coarse harmonized value into invented finer cells.
- Keep observed counts and harmonized estimates explicitly separate, including their time bases. The observation view uses UTC acquisition dates, while the existing harmonized calendar uses local civil dates and exclusions.
- Retaining archived observations on dates omitted from the harmonized calendar is defensible only when that difference is visible. Counts must not be claimed to reconcile across the two views.
- Restrict this release to known presumed-vegetation records with VIIRS nominal/high confidence, valid coordinates and timestamps. Unknown fire type is not presumed vegetation.
- Keep absent FRP and footprint dimensions unavailable rather than converting them to zero. Reported FRP is sampled radiative power, not energy, severity, burned area or an identification of human cause.
- A nominal 375 m sensor pixel and a plotted coordinate do not establish an exact fire location or perimeter. Marker size is schematic. Scan/track dimensions alone do not establish an exactly oriented ground polygon.
- Preserve detection multiplicity. Repeated detections can describe the same fire, and a single detection can include multiple fires.
- An empty month or tile means no qualifying archived detection, not verified absence of fire or complete observation coverage.
- New grids must conserve exact eligible counts, including negative-coordinate and exact-boundary cases. Coordinate precision must not silently change.

## Independent source scan

The reviewer read the original seven CSVs using a separate chunked analysis, without importing the new producer. Every source row count matched `reports/data_manifest.json`. All eligible records had valid timestamps and coordinates, positive finite scan/track dimensions, nonnegative finite FRP, and an S-NPP satellite identifier.

| Country | Original archive rows | Eligible vegetation nominal/high detections |
| --- | ---: | ---: |
| Nepal | 53,913 | 48,157 |
| United States | 484,736 | 387,620 |
| Bangladesh | 8,083 | 6,877 |
| Egypt | 27,178 | 7,931 |
| Australia | 979,867 | 881,613 |
| India | 552,312 | 382,884 |
| Brazil | 1,935,740 | 1,767,650 |
| Total | 4,041,829 | 3,482,732 |

These are acquisition-year archive counts. They are not counts of distinct fires or calendar-aligned converted values.

## Complete independent source-to-export comparison

The reviewer independently compared all **3,482,732** exported observations with the seven original CSVs, without importing the observation producer. This was a full comparison, not a sample or a check against the producer's own receipt.

- Recomputed the eligible counts, every occupied 0.05-degree month-grid bin, all 366 daily record counts per country, and explicit zero-record dates from source rows.
- Verified every source archive SHA-256 against both the original manifest and the public index.
- Compared all eight published point fields: latitude, longitude, UTC acquisition time, confidence, scan, track, FRP and day/night. Order-independent per-month row fingerprints used row count plus SHA-256 sums and XORs, preserving repeated-row multiplicity. Nepal also received a direct full tuple-multiset comparison: zero missing or extra records.
- Checked every point tile's hash, count, identity/context and geographic bounds; all points lie inside their declared bounds and no tile exceeds 8,000 records.
- Verified monthly hashes and contracts through the browser decoder across all 84 month files. Grid sums, tile sums and source-filtered month counts agree exactly.
- Confirmed Nepal August and September have explicit zero-record payloads matching the source. They remain unknown-coverage cases, not evidence that no fires occurred.

| Country | Source-field and multiplicity comparison | Exported point tiles |
| --- | --- | ---: |
| Australia | Passed, 881,613 records | 1,889 |
| Bangladesh | Passed, 6,877 records | 74 |
| Brazil | Passed, 1,767,650 records | 2,599 |
| Egypt | Passed, 7,931 records | 246 |
| India | Passed, 382,884 records | 1,051 |
| Nepal | Passed, 48,157 records | 76 |
| United States | Passed, 387,620 records | 2,846 |

An initial Nepal fingerprint assertion exposed an issue in the review harness: empty expected-month keys were compared with absent actual-month keys. Direct tuple comparison and explicit zero-month comparison resolved it; no exported data change was required.

## Storage finding and resolution

An independent count of occupied country/month/geographic storage tiles found 24,407 files with 1-degree tiles, exceeding Cloudflare Pages' free-plan file limit even before existing assets. Two-degree storage tiles require 8,519 files. The reviewer recommended 2-degree storage tiles; this changes file packaging only, not coordinate precision or the 0.05-degree display grid.

| Country | 1-degree storage tiles | 2-degree storage tiles |
| --- | ---: | ---: |
| Nepal | 171 | 73 |
| United States | 8,029 | 2,834 |
| Bangladesh | 148 | 74 |
| Egypt | 523 | 246 |
| Australia | 4,767 | 1,845 |
| India | 3,053 | 1,042 |
| Brazil | 7,716 | 2,405 |

The implementation now uses 2-degree base tiles with adaptive subdivision of dense tiles. The final independent inventory is **8,866 JSON files, 244,970,711 bytes**. The largest is `Brazil/2024-09.json`, **686,483 bytes**, well below the 25 MiB asset limit. The total includes 8,781 point tiles, 84 month files and the index. These are selected country/month and spatial downloads, not one startup payload.

Index SHA-256 independently verified: `3379a22ad49bc0041721a1bc2b93bb71f2d0bfce95e8deefa60acf0879c0f2d6`.

No local source paths were found in public observation JSON. The tracked working diff at review time contained no modifications to existing scientific datasets, pipeline files or reports; the observation producer, exports and documentation are additive. The integration changes in existing UI files expose the separate layer and accurately distinguish its scale.

## Geometry, loader and renderer review

The reviewer added `web/tests/observation-viewport.mjs`, using an independent camera-basis projection to check that the spherical view cap does not omit visible surface points. It covers 100 location/distance/aspect configurations, including close zoom, the antimeridian and polar views. Separate cases exercise edge tiles, far-side exclusion from the view cap, repeated zoom and invalid numeric bounds.

The review found that invalid `maxDistance` values could produce NaN or inside-Earth zoom results. The parent fixed validation; all five independent geometry tests now pass. These are geometry tests, not claims of physical-phone testing or end-to-end ray-picking coverage.

The combined focused command passed **17 tests**:

```powershell
node --test web/tests/observation-detail.mjs web/tests/observation-viewport.mjs
```

The loader/control cases cover coordinate and timestamp preservation; zero versus null values; invalid context, dates and measurements; count conservation; failed hashes; aborted and stale requests; bounded concurrency; duplicate identities; retry behavior; explicit scientific wording; evidence focus; country-change races; and the actual seven-country/84-month artifacts.

The renderer source review verified these safeguards:

- Native points come from original coordinates; the overview grid counts observed records. No interpolation or artificial harmonized subcells are produced.
- An 80,000-point request budget retains the complete grid and requests closer zoom rather than sampling away observations.
- Selected evidence is keyed to country/month, so it cannot remain under a different selection. Original archive links are passed to the controls.
- Point/grid picking rejects geometry behind Earth. Camera controls update after bounded zoom; the small near-clip distance supports close viewing.
- Empty/loading/error states remain separate. The table offers access without a functioning WebGL context.
- The existing harmonized Earth is a separate renderer/layer with its own historical year and scientific values.

A further real-data budget check sampled the 30 busiest cells of every country/month at minimum zoom for phone and desktop aspect ratios: **4,606 cases, none over budget**. The largest nearby request was 28,949 observations in Brazil, October. This supports the fallback's practical usefulness in dense data; it is not a browser performance benchmark or proof for every possible camera position.

## Scientific conclusion and remaining limits

The finer layer is scientifically defensible as a view of archived observed detections. It is **not** a new fine-resolution harmonized product, validated fire-boundary map, or operational fire alert service. It makes neither an observational-completeness claim nor a NASA approval claim.

The deliberate difference in UTC/raw versus local-date/outage-masked totals is visible in the controls. Retaining those source detections is acceptable under that explicit contract. No equality with harmonized totals should be implied later.

The 0.05-degree cells represent counts, not equal-area density; their ground area varies with latitude. A nominal 375 m pixel does not give a precise fire boundary. Marker sizes are schematic, repeated points may overlap, and the contextual coastline remains a map aid rather than 375 m geographic imagery. FRP remains a sampled radiative-power measurement, not energy, severity, burned area or evidence of human cause.

Integration must still verify the actual desktop and phone-width flows, repeated zoom, pinch/tap interaction, country/month switching, Nepal's empty months, table-to-3D restoration, and return to the harmonized overview. The parent agent owns those browser checks and the complete build/test result; consult its final verification record rather than treating this source/data review as a substitute.

## Source interpretation

- NASA VIIRS attributes: https://firms.modaps.eosdis.nasa.gov/content/descriptions/FIRMS_VIIRS_Firehotspots.html
- NASA MODIS attributes: https://firms.modaps.eosdis.nasa.gov/content/descriptions/FIRMS_MODIS_Firehotspots.html
- Cloudflare Pages limits: https://developers.cloudflare.com/pages/platform/limits/
