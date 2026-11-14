# FIRETRACE

Compare satellite fire observations on a named reference scale, inspect seasonal patterns, and trace every chart back to its evidence.

This initial implementation uses NASA FIRMS annual country archives for **Nepal and the United States**. MODIS Terra, MODIS Aqua and VIIRS S-NPP remain separate during cleaning and scientific evaluation. The app presents converted VIIRS detections on an **Aqua-equivalent scale**, with transparent baseline comparisons. Hotspots are observations, not a true count of independent fires.

## What's implemented

- Public archive downloader with atomic transfers, CSV checks, checksums and a source manifest.
- Confidence/type filtering, IANA civil time, geographic grid cells, diagnostics and Parquet output.
- Raw VIIRS baseline, global-ratio calibration and region/day-night/FRP-stratified calibration.
- Model selection using 2018–2019 validation data; monthly and weekly evaluation on 2020–2024 test years.
- Training-year bootstrap calibration intervals, separate from total observation uncertainty.
- Country calendar, seasonal profile, historical unusual-period flags, evidence drawer, cell selection and CSV/ICS exports.
- Separate per-stream weekday analysis, corrected null tests and explicit research release gate.
- Synthetic sensor-switch verification, unit tests and scientific/submission documentation.

The initial supported complete local-calendar years are **2013–2024**. The adjacent 2012 and 2025 UTC archives supply local-date edges. This release does not claim a validated 2000-present record, a Terra-to-Aqua historical bridge, global geographic coverage or a forecasting service.

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

`--reuse-clean` explicitly reuses `data/processed/detections.parquet`; omit it after changing raw files or cleaning logic. `--reuse-analysis` additionally reuses existing analysis results and is appropriate only for rebuilding presentation/export layers without scientific changes.

To reproduce from existing raw archives, run `python -m pipeline.run_all` without download or cache flags. To fetch a different configured set, use `--download --countries Nepal United_States Bangladesh --years 2012 2025`. Rebuild caches after extending the data. Network downloads may take time and require permission in restricted environments.

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
| `reports/kill_test_gate.json` | Optional rhythm module's explicit release decision |
| `reports/kill_test_results.csv` | Main/daytime/control estimates, including unsuccessful results |
| `reports/build_summary.json` | Actual built scope, row counts, label and runtime |

The release gate requires the US replication check plus at least two other countries, each with two qualifying streams, and the specified diagnostic qualifications. A two-country build cannot pass that gate. Estimates can still be examined in research reports; the web application must not promote them as a confirmed discovery.

## Scientific limits

Complete archive downloads do not prove complete satellite observation coverage. A zero archived detection count means no qualifying record was present, not that the satellite observed fire-free land. Cloud, acquisition gaps, changing instruments and mismatched FRP measurement scales remain limitations.

Calibration is assessed against Aqua, not independent ground truth. Bootstrap bands describe calibration variability; they omit other uncertainty sources. The cell browser exposes a small training-selected subset of occupied cells, while country totals use all analyzed cells. Critical periods describe historical activity and are not emergency advice or forecasts.

See `METHODS.md`, `LIMITATIONS.md` and `DECISIONS.md` for the complete methodology and scope decisions.

## Deploy

**Live application:** [FIRETRACE on Cloudflare Pages](https://firetrace-bhaktapur-2026.pages.dev/).

The application is deployed as static assets on Cloudflare Pages, with no paid compute or database provisioned. The public URL does not require sign-in. See `DEPLOYMENT.md` for the verified deployment and update commands.

Run `npm ci --prefix web` once, then `npm run build` from the repository root to generate root `dist`. The included precomputed data supports this build without downloading or rerunning the scientific pipeline. Running `npm run build` inside `web` instead generates `web/dist`.

The working copy also retains `.openai/hosting.json` for the earlier private Sites preview. Do not reuse its project identity when creating a different team's Site.

## Attribution

Data: [NASA FIRMS](https://firms.modaps.eosdis.nasa.gov/country/). Weekly-cycle research motivation: [Earl, Simmonds and Tapper (2015)](https://doi.org/10.1002/2015GL066383). Software: MIT; external data and dependencies retain their applicable terms. See `AI_DISCLOSURE.md` for AI assistance.

**NASA does not endorse this project.**
