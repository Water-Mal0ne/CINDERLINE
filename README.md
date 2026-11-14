# FIRETRACE

Compare satellite fire observations on a named reference scale, inspect seasonal patterns, and trace every chart back to its evidence.

The harmonized calendar uses NASA FIRMS annual country archives for **Nepal and the United States** only. The human-rhythm analysis covers **seven countries** (United States, Australia, Brazil, India, Nepal, Bangladesh, Egypt; 2013–2024). MODIS Terra, MODIS Aqua and VIIRS S-NPP remain separate during cleaning and scientific evaluation. The app presents converted VIIRS detections on an **Aqua-equivalent scale**, with transparent baseline comparisons. Hotspots are observations, not a true count of independent fires.

## What's implemented

- Public archive downloader with atomic transfers, CSV checks, checksums and a source manifest.
- Confidence/type filtering, IANA civil time, geographic grid cells, diagnostics and Parquet output.
- Raw VIIRS baseline, global-ratio calibration and region/day-night/FRP-stratified calibration.
- Model selection using 2018–2019 validation data; monthly and weekly evaluation on 2020–2024 test years.
- Training-year bootstrap calibration intervals, separate from total observation uncertainty.
- Country calendar, seasonal profile, historical unusual-period flags, evidence drawer, cell selection and CSV/ICS exports.
- Rotatable 3D Earth with 15,118 real grid cells, annual history, a fixed color scale, exact-value inspection and an accessible table fallback.
- Three-series monthly comparison, keyboard inspection, monthly CSV export, anomaly filtering and sorting, and calendar exports with concrete dates.
- Shareable links restore country, dates, daily cell, display scale and open evidence week. The Earth renderer sleeps when idle or offscreen and offers a table fallback.
- Human rhythm view for seven countries, separate from the Nepal/US calendar: the official pre-registered decision, weekday charts per country and stream with 95% intervals, stricter robustness checks, a negative control and an exploratory per-cell map.
- Synthetic sensor-switch verification, unit tests and scientific/submission documentation.

The supported complete local-calendar years are **2003–2024**: observed Aqua through 2012, converted VIIRS from 2013. The cached input snapshot contains 76 official annual archives and 10,142,672 cleaned records. Adjacent UTC archives supply local-date edges. This release does not claim a validated 2000-present record, a Terra-to-Aqua historical bridge, worldwide observation coverage or a forecasting service.

## Run locally

Requirements: Python 3.11+ and Node.js 20+. A project-local `.venv` is already prepared in the working copy used to build this release; it is not committed or distributed in the source archive.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pipeline.run_all --download
cd web
npm ci
npm run dev
```

On macOS/Linux, use `.venv/bin/python` instead. Run analysis commands from the repository root. For the already-prepared Windows working copy:

```powershell
.\.venv\Scripts\python.exe -m pipeline.run_all --reuse-clean
```

`--reuse-clean` explicitly reuses `data/processed/detections.parquet` and its saved source manifest. Newly downloaded archives are not attached to an older cache. Omit this option after changing raw inputs or cleaning logic. `--reuse-analysis` additionally reuses existing analysis results only when input and analysis-code fingerprints match; it is appropriate for rebuilding presentation/export layers without scientific changes.

To reproduce from existing raw archives, run `python -m pipeline.run_all` without download or cache flags. To fetch a different configured set, use `--download --countries Nepal United_States Bangladesh --years 2012 2025`. Rebuild caches after extending the data. Network downloads may take time and require permission in restricted environments.

To rebuild the human-rhythm results from the seven-country archives (same folder layout as `pipeline/download.py`):

```powershell
python reference/kill_test.py data --label "REAL FIRMS DATA"          # official gate -> copy outputs to reports/official/
python reference/rhythm_map.py data                                 # exploratory per-cell map -> reports/official/
python reference/export_rhythm_input.py data data/processed         # cleaned detections for the robustness run
python -m pipeline.rhythm data/processed/rhythm_input_7countries.parquet --manifest data/processed/rhythm_input_manifest.json --official reports/official --output reports/rhythm_robustness
python -m pipeline.rhythm_web                                       # writes web/public/data/rhythm.json
```

Synthetic checks remain separate:

```powershell
.\.venv\Scripts\python.exe -m pipeline.run_all --synthetic
.\.venv\Scripts\python.exe -m pytest tests -q
cd web
npm run build
```

Synthetic web JSON goes to `work/synthetic-web-data`, not the production data directory. `reports/synthetic_switch.png` is always explicitly labeled synthetic.

## Read the evidence

| File | Meaning |
|---|---|
| `reports/data_manifest.json` | Source URLs, transfer status, SHA-256 hashes and archive years |
| `reports/cleaning_diagnostics.json` | Filtering, invalid coordinates/times and timezone diagnostics |
| `reports/harmonization_eval.csv` | Baselines and calibrated models, split by country and time aggregation |
| `reports/harmonization_model.json` | Fitted ratios, model choice, periods and uncertainty definition |
| `reports/official/kill_test_gate.json` | Official pre-registered rhythm decision (7 countries) |
| `reports/official/kill_test_results.csv` | Official per-country, per-stream weekday estimates with per-day 95% intervals |
| `reports/official/RESULTS.md` | Plain-language write-up of the rhythm result and the exploratory map |
| `reports/rhythm_robustness/robustness_checks.json` | Stricter re-analysis, reported as robustness checks only |
| `reports/official/rhythm_cells.geojson` | Exploratory per-cell rest-day map (VIIRS, with Aqua check) |
| `reports/kill_test_*.json`, `reports/rhythm_results.json` | Earlier Nepal/US-only rhythm run, superseded by `reports/official/` |
| `reports/build_summary.json` | Actual built scope, row counts, label and runtime |

## Human rhythm result

The official decision comes from the pre-registered test in `reference/kill_test.py`, run on real FIRMS data for seven countries (outputs in `reports/official/`). The rule, fixed before the data were analysed: the United States replication check must pass and at least two other countries must pass, where a country passes if its predicted rest day is the lowest weekday and significant after Bonferroni correction in at least two of Terra, Aqua and VIIRS.

**Decision: pass.** The United States (3 of 3 streams), Australia (3 of 3) and Brazil (2 of 3) pass. India, Nepal, Bangladesh and Egypt do not. All three passing countries rest on Sunday; Friday- and Saturday-rest countries did not show a dip, so this does not show the dip following each country's own rest day. A dip is consistent with people scheduling their burning; it is not proof of cause.

`pipeline/rhythm.py` re-analyses the same detections with stricter rules (only years with both neighbouring archives, 95% upper bound below 1, matched per-country static-source controls). These are reported as robustness checks next to the official decision and never change it. All three passing countries meet all three checks; under the strict rules Australia and Brazil hold in 2 of 3 streams (`reports/rhythm_robustness/`).

The per-cell map (`reference/rhythm_map.py`) is exploratory and not part of the pre-registered test.

## Scientific limits

Complete archive downloads do not prove complete satellite observation coverage. A zero archived detection count means no qualifying record was present, not that the satellite observed fire-free land. Cloud, acquisition gaps, changing instruments and mismatched FRP measurement scales remain limitations.

Calibration is assessed against Aqua, not independent ground truth. Bootstrap bands describe calibration variability; they omit other uncertainty sources. The globe uses annual totals for all 15,118 reference-stream occupied cells. Daily drill-down exposes 12 training-selected cells per country, while country totals use all analyzed cells. Detailed cell files load on demand. Climatology and anomalies use complete seven-day periods only; the final one- or two-day period remains visible in the calendar but is excluded from those comparisons. Critical periods describe historical activity and are not emergency advice or forecasts.

See `METHODS.md`, `LIMITATIONS.md` and `DECISIONS.md` for the complete methodology and scope decisions.

## Deploy

**Live application:** [FIRETRACE on Cloudflare Pages](https://firetrace-bhaktapur-2026.pages.dev/).

**Source repository:** [Water-Mal0ne/FIRETRACE](https://github.com/Water-Mal0ne/FIRETRACE) (public).

The application is deployed as static assets on Cloudflare Pages, with no paid compute or database provisioned. The public URL does not require sign-in. See `DEPLOYMENT.md` for the verified deployment and update commands.

Run `npm ci --prefix web` once, then `npm run build` from the repository root to generate root `dist`. The included precomputed data supports this build without downloading or rerunning the scientific pipeline. Running `npm run build` inside `web` instead generates `web/dist`.

The working copy also retains `.openai/hosting.json` for the earlier private Sites preview. Do not reuse its project identity when creating a different team's Site.

## Attribution

Data: [NASA FIRMS](https://firms.modaps.eosdis.nasa.gov/country/). Weekly-cycle research motivation: [Earl, Simmonds and Tapper (2015)](https://doi.org/10.1002/2015GL066383). Software: MIT; external data and dependencies retain their applicable terms. See `AI_DISCLOSURE.md` for AI assistance.

Globe land and borders: public-domain [Natural Earth](https://www.naturalearthdata.com/about/terms-of-use/), distributed through world-atlas 2.0.2. The globe is rendered with Three.js. Map shading outside the supported countries does not represent fire observations.

**NASA does not endorse this project.**
