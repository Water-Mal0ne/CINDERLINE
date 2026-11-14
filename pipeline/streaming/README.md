# Exact-count processing

This additive route processes annual FIRMS archives in bounded chunks. The original `pipeline.run_all` raw-record route remains available. The count route never expands multiplicities into individual detections.

From the repository root:

The complete official-archive-to-website workflow is one command:

```powershell
.venv\Scripts\python.exe -m pipeline.streaming reproduce --output work/fresh-reproduction --model-revision seven-country-v1 --baseline-commit 841998b --baseline-reports reports/releases/two-country-841998b
```

It downloads the seven countries' MODIS 2001–2025 and Suomi-NPP VIIRS 2012–2025 country archives with three workers and a 10 GiB disk reserve, prepares exact counts, builds the scientific outputs, regenerates the controlled synthetic switch check and separate prespecified 0.5° grid/Terra bridge validation, installs the locked frontend dependencies in an isolated directory, regenerates map context and builds the complete site. The resulting site is under `work/fresh-reproduction/site/web/dist`. Supplemental validation is under `pipeline/scientific_validation`; it does not change the frozen country choices or publish a Terra reconstruction. The command checks actual total and individual file sizes and never deploys or replaces the current app.

To reproduce the current locked release from existing official archive paths without rerunning selection or held-out evaluation:

```powershell
.venv\Scripts\python.exe -m pipeline.streaming reproduce --output work/locked-reproduction --source-manifest reports/data_manifest.json --locked-evaluation reports --model-revision seven-country-v1 --baseline-commit 841998b --baseline-reports reports/releases/two-country-841998b
```

The source manifest's absolute archive paths must exist locally. On a fresh checkout, omit `--source-manifest` to download official archives. `--locked-evaluation` requires matching archive fingerprints and verified artifact hashes; revised official archive bytes require a new explicitly recorded model revision. Node/npm and the Python requirements must be installed. The command preserves failed-run artifacts; reuse their archive manifest with a new output directory to continue without downloading completed files again.

Individual stages remain available:

```powershell
.venv\Scripts\python.exe -m pipeline.streaming prepare --manifest data/raw/manifest.json --countries Nepal United_States Bangladesh Egypt --output work/prepared-four
.venv\Scripts\python.exe -m pipeline.streaming prepare --manifest work/additional-country-archives/manifest.json --countries Australia India Brazil --output work/prepared-three
.venv\Scripts\python.exe -m pipeline.streaming build --preparations work/prepared-four work/prepared-three --expected-countries Nepal United_States Bangladesh Egypt Australia India Brazil --baseline-reports reports --output work/seven-country-build
```

`--write-clean` optionally preserves exact cleaned detection partitions. It is unnecessary for normal processing because the original archive bytes and their hashes remain available. Completed preparations cache source/code hashes and chunk options. Builds require a new output directory to preserve prior model choices and reports. `build --analyses ...` can reuse verified reductions whose manifest exactly matches the preparations.

Outputs include the source manifest, preserved baseline report hashes, training/validation selection lock, held-out evaluation, 200-draw calibration intervals, per-country harmonized Parquet files, weekly tests and controls, all-cell annual globe, regional metadata, calendar exports, and public JSON. Global ratios are refitted for the declared country scope; the model revision records that scope and archive fingerprint.

Complete MODIS 2002–2025 and VIIRS 2012–2025 archives are required for every requested country's full 2003–2024 display. Adjacent UTC files establish archive completeness only. They do not measure actual satellite or cloud observation coverage. The first eligible complete years remain Terra 2001, Aqua 2003 and VIIRS 2013; the source records determine which years can qualify. No Terra reconstruction is introduced.

Calibration retains train 2013–2017, validation 2018–2019 and held-out test 2020–2024. All country choices are persisted before test evaluation. The weekly algorithm preserves the seeded resampling, weekday exposure correction, fixed 21-test family and matched controls. Synthetic provenance always prevents a real-data release claim.

`public/data` uses `column-dictionary-v1`. A table has `encoding`, `columns`, `rows`, and a `dictionaries` map keyed by column name. Only dictionary columns contain integer indexes; all other values remain unchanged. National `daily_compact` normalizes back to `daily` records. Exact JSON roundtrip checks cover every row before files are written. The globe and CSV/ICS exports remain unchanged. The original-format payload is also retained under `public_original/data` for comparison.

The build measures total static size and the largest individual file. It returns exit code 2 when the projected static size exceeds the 50 MiB target. The individual Cloudflare Pages target is 25 MiB per file. The projection includes current compiled frontend assets and shared map files, so the final frontend build must check the actual deployment size again. This command generates local artifacts and does not deploy or replace production data.
