# Independent release-quality check

Date: November 14, 2026. A separate checking agent inspected the phase-2 release and then the final share-link and demand-rendering integration. Scope: source, scientific contracts, failure paths, packaging and automated tests. The coordinator owns browser rendering and interaction verification.

## Final automated evidence

- Python regression suite: **39 passed** in 4.18 seconds.
- `npm --prefix web test`: **passed** — client data contract, anomaly filtering/sorting, demand rendering, and all **26** share-state/integration tests.
- `npm --prefix web run typecheck`: **passed**.
- Published-payload reconciliation: **1,462,692 numerical checks passed**, two regions, **38,965,974 bytes** of static data.
- Credential-pattern scan: **135 tracked and unignored text files** checked; no matching filenames. The scan checked private-key headers, common GitHub/AWS credential forms and quoted credential assignments. This is a bounded pattern scan, not a guarantee against every possible secret format; no values were printed.
- The coordinator reports a clean final diff check after trimming App's final blank line and marking required calendar CRLF correctly.

The independent source review found no numerical or functional release blocker in the current Nepal/US scope. Automated checks alone do not prove visual quality or every browser failure path.

## Scientific and data-contract checks

Separate instrument streams, the named Aqua reference, source-aware early history, complete-week anomaly qualification, held-out model evaluation, the disabled rhythm gate and explicit synthetic labels remain intact. The payload verifier reconciles national and detailed daily records with saved analysis outputs and annual globe totals with the national record.

The globe uses 0.25-degree grid footprints, actual grid centers, country-qualified cell IDs and a fixed all-year logarithmic scale. Daily drill-down strips the country prefix before lookup. Missing values remain distinct from recorded zero. The accessible table explicitly shows the top 20 cells for the selected region/year; it does not expose every annual cell.

`CONTRACTS.md` agrees with the published national inline records and compact lazy-cell payloads. The release still contains Nepal and the United States, 2003–2024; wider downloaded archives are not represented as processed coverage. There is no claim of operational prediction, distinct fire counts or a 2000–2002 Terra reconstruction.

## Integration and recovery

- Share links allowlist region and daily-cell IDs, validate civil dates, recover invalid/unsupported settings with notices, and restore an evidence week only from actual filtered rows. Links explicitly use current published data rather than immutable snapshots. Camera position, annual-cell selection and Earth/table choice are deliberately excluded and explained.
- App prevents sharing while the requested series or linked evidence is unresolved. Region and cell fetches check abort state before applying results. Whole-region recovery clears a failed cell's stale error without clearing a genuine missing-region error.
- Clipboard failure retains a selectable URL; asynchronous copy results cannot overwrite a newer selection's state. Copy links discard unrelated query parameters and fragments.
- Demand rendering coalesces changes, continues OrbitControls damping, stops when idle or outside the viewport/hidden document, and resumes on a visible invalidation. Cleanup cancels pending work. Tests cover synchronous invalidation during a frame as well as late callbacks after disposal.
- Both WebGL construction failure and runtime context loss switch to the regional grid table. The latter preserves data and offers a 3D retry. These paths were source-inspected; this checking agent did not simulate graphics failure in a browser.

Earlier fixes authorized for this checking agent were limited to `web/src/App.tsx`: stale lazy-cell error recovery and correct N/S/E/W sidebar coordinate labels. The coordinator separately corrected grid-center coordinates and integrated the final renderer/share work.

## Browser evidence and remaining follow-up

The coordinator reports that a US daily-cell link (`40.75:-123.50`) restored the raw scale, 2020 range and open evidence week beginning 2020-09-30 after reload and fresh navigation; an unknown-country link showed an explicit fallback notice and Nepal; the share panel fit a 390px mobile viewport; and the globe responded to zoom/year controls after becoming idle and returning from an offscreen position. Final real cell picking, orbit, graphics failure and download evidence remain part of the coordinator's release record.

One keyboard-accessibility issue was reported during the final review: closing share details could unmount the focused close button without returning focus to the trigger. The coordinator fixed it and verified in the browser that Escape closed share details, restored focus to “Share this view”, preserved the evidence dialog and produced no console errors. No implementation change was made by this checking agent during the final source freeze.

After deployment, refresh the deployment record and source package so their revision and coverage match the published build. The build script restricts its replacement output directory to the repository's own `dist`; staging, raw archives, local credentials and dependencies are excluded by the repository ignore rules.

## Separate expansion gate

The seven-country work remains isolated. The checking agent identified a commissioning-year caveat: adjacent archives alone could incorrectly qualify partial Aqua year 2002 after additional historical files arrive. The data agent reports a fix in `work/phase3/weighted_rhythm.py`: qualification requires Terra >= 2001, Aqua >= 2003 and VIIRS >= 2013 before archive/local-period evidence can qualify a year. Its regression rejects Aqua 2002 and accepts 2003. That staged change is not evidence that seven-country scientific validation has completed, and it is not part of this Nepal/US publication.
