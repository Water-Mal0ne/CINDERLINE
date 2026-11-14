# Web implementation status

## Phase 2: evidence journey and Earth explorer

Integrated all four landing sections while preserving source labels and the rhythm gate:

- Section 1 now contains a lazy-loaded Three.js Earth with actual spherical grid patches, annual timeline linked to calendar dates, country focus/global view, orbit/zoom, cell picking and accessible grid-table fallback. It uses supplied land/coastline geometry, a fixed all-year logarithmic color scale, and explicit zero versus unprocessed coverage labels. No automatic spinning or invented global fire coverage.
- A short evidence journey shows a real illustrative week using only shared converted-VIIRS/Aqua daily records. It links to full-record comparison, the exact evidence card and held-out results; its selection is explicitly not a model-performance test.
- Section 2 integrates the coordinator's enhanced `ComparisonChart`: raw baseline, Aqua-equivalent record, observed Aqua, keyboard month inspection, source-era explanation, monthly table and export.
- Section 3 integrates the data agent's `SeasonalContext` with keyboard inspection and date-aware critical periods.
- Section 4 integrates the QA agent's `AnomalyPanel` with filters, sorting and load-more controls.
- Region and cell JSON are cached in bounded session memory. Per-cell data loads on demand, supporting both object-array and compact column/row formats.
- Heatmap navigation uses one tab stop with arrow-key movement and Enter to inspect evidence.
- Evidence cards no longer apply regional anomalies to cells or partial weeks. Direct-Aqua intervals say calibration is not applicable, rather than suggesting zero observation uncertainty.

Phase 2 validation: TypeScript passed; data-contract and anomaly tests passed; Vite 6.4.6 production build passed. The main application is approximately 68 KB gzip and the separate Three.js globe chunk 141 KB gzip. Final browser checks and publication are coordinated by the parent agent. Final rebuild follows any remaining QA fixes or generated-data updates.

Implemented a Vite + React + TypeScript application using the shared precomputed JSON contract. No mock observations are shipped.

## Working features

- Region, date-range and processed-grid-cell selection.
- Geographic SVG plot of actual supplied cell coordinates, with the pipeline's cell-scope disclosure.
- Year/week heatmap, shared raw/harmonized color scale, and keyboard-accessible week evidence buttons.
- Monthly raw/reference-scale comparison and regional historical seasonal bands.
- Critical-period display, CSV download and calendar ICS export.
- Anomaly list linked to evidence cards.
- Evidence drawer with per-stream observations, daily estimates/intervals, source, model and coverage.
- Evaluation tables, gated rhythm view, methods, limitations and source links.
- Persistent dataset labeling, visible synthetic warning, unknown-value handling and human-readable load errors.
- Responsive styling, keyboard focus states, drawer focus containment/Escape, skip link and reduced-motion support.

## Validation

- `npm run build`: TypeScript and Vite production build passed. Approximately 190 KB JS / 61 KB gzip before data payloads.
- `npm test`: passed calendar boundaries, unknown values, grouped totals, CSV labeling/escaping and ICS end-of-year boundaries.
- Local server returned HTTP 200 for `/` and `/data/index.json`.
- Real Nepal payload was inspected against the contract: 4,383 daily rows, 12 supplied cells, M1 model, and an insufficient-data rhythm gate.
- Parent coordinator performed browser QA. Final rebuild is required after data generation completes.

## Implementation decisions

- Geographic SVG replaces MapLibre, avoiding external map tiles and extra network dependencies. It shows supplied cell locations, not a geographic boundary map or a claim of complete spatial coverage.
- Calendar bins match the Python pipeline: seven-day bins anchored on January 1; the final bin can be shorter. ICS events are clipped at the next January 1.
- Historical seasonal summaries and anomalies remain region-level. Cell-specific daily data and evidence are available separately.
- Default JSON load failures do not generate synthetic replacements.

## Preview

`http://127.0.0.1:5173/`

Retained execution session: `60250`. Start command: `node node_modules/vite/bin/vite.js --host 127.0.0.1 --port 5173 --strictPort`.

On this Windows host, Vite's config resolution required running the build/dev command outside the filesystem sandbox. Dependencies were installed with authorized network access after the initial sandboxed helper stalled.
