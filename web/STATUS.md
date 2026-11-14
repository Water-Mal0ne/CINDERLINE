# Web implementation status

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
