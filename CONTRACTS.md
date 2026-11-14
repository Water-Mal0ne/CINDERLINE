# FIRETRACE implementation contracts

All paths relative to repository. Python 3.11+; precomputed data, no server API.

## Ownership
- data agent: pipeline/download.py, clean.py, harmonize.py, synthetic.py; tests/test_data.py, test_harmonize.py; requirements.txt. Owns real data acquisition and harmonization reports.
- rhythm agent: pipeline/rhythm.py, tests/test_rhythm.py, scientific docs METHODS.md and LIMITATIONS.md.
- web agent: web/ source and package files; do not change public/data once integration begins.
- coordinator: pipeline/calendar.py, run_all.py, shared config, exports, README, submission, deployment.

## Python APIs
`download.download(countries, years, sensors, data_dir)` writes manifest; CLI may provide more options.
`clean.load_clean(data_dir)` returns pandas detections frame, writes diagnostics as appropriate. Required columns: country, stream (Terra/Aqua/VIIRS), utc, local, local_date, weekday (Mon=0), year, lat, lon, cell_id, frp, daynight, type, confidence. Unknown coverage must not be inferred from no detections. Preserve type 1/2.
`harmonize.run(detections, output_dir)` returns harmonized dataframe and evaluation dataframe. Harmonized: date ISO, region country, cell_id (ALL or grid id), raw_terra, raw_aqua, raw_viirs, harmonized, lo, hi, coverage string, source string, model string. Monthly/weekly holdout evaluation in reports/harmonization_eval.csv. Include synthetic/real labeling.
`rhythm.run(detections, output_dir, label='REAL FIRMS DATA', manifest=None)` returns JSON-serializable dict {gate, countries, diagnostics, controls}. Countries keyed country; each contains streams list with stream, weekdays array of 7 {day,index,lo,hi}, years, rest_day, p_adjusted, status. Gate decision pass/fail/insufficient_data; never silently manufacture data. Expose confidence/coverage caveats.

## Exact-count pipeline

`python -m pipeline.streaming prepare` verifies and cleans manifest-named archives in bounded chunks. `build` reduces exact multiplicities, locks training/validation choices, evaluates held-out years, generates per-country Parquet and annual globe/calendar outputs, and applies the optional lossless dictionary codec. Its output directory must be fresh and is not implicitly deployed. The source manifest, model revision and locked selections travel with the output. Reusing a saved evaluation requires matching source identity; publication must not trigger model reselection.

Count partitions retain `n`, and consumers must sum `n`; counting aggregate rows is incorrect. Commissioning and adjacent-archive requirements precede complete-year eligibility. National/daily/global annual totals must reconcile to the same model and source snapshot. Final data plus frontend/map assets must meet the 50 MiB static target, and each served file must remain below the 25 MiB hosting limit.

## Web JSON
`web/public/data/index.json`: {label: string, regions: [{id: 'Nepal', name: 'Nepal', file: 'Nepal.json'}], generated_at: ISO, limitations: string[]}.
`web/public/data/{region}.json`: {meta: {region, name, label, period_start, period_end, reference:'MODIS Aqua', model, coverage_note, sources: [{name,url}], centroid:[lon,lat]}, daily:[{date,cell_id:'ALL',raw_terra,raw_aqua,raw_viirs,raw, harmonized,lo,hi,coverage,source,model}], weekly_climatology:[{week,median,p10,p90,critical}], anomalies:[{date,week,value,z_score,status}], critical_periods:[{start_week,end_week,label}], rhythm:null|{gate,streams,rest_day}, eval:[{model,region,split,aggregation,bias_pct,mae,correlation,peak_week_error}], cells:[{id,lat,lon,daily:[same daily]}]}.
The shape above describes the normalized in-memory region. The seven-country publisher stores national records under `daily_compact` instead of `daily`. Each of the twelve training-selected cells has `{id, lat, lon, file}`; `file` points to a portable relative path under `data/cells/`. Both national and detailed tables use `{encoding: "column-dictionary-v1", columns: string[], rows: unknown[][], dictionaries?: {[columnName: string]: unknown[]}}`. A row value is an integer dictionary index only for a column present in `dictionaries`; every other value is literal. The encoder preserves original JSON values and types, including zero, null and float precision. The client rejects unknown encodings, malformed rows and invalid dictionary indexes, and normalizes national records back to `daily` before UI use. A region cannot contain both `daily` and `daily_compact`.

The reader remains compatible with legacy national/inline `daily` and plain `{columns, rows}` cell tables. Cell coordinates are grid centers; occupied-cell counts and the selected-cell limitation are explicit in `meta`. The annual globe and CSV/ICS formats do not use this dictionary codec.

`web/public/data/globe.json` supplies the annual 0.25-degree grid for every published reference-stream cell, independently of the twelve daily drill-down cells. It contains years, scale/unit metadata, country summaries and compact cell records. The frontend uses a fixed all-year logarithmic color scale; unknown values are distinct from zero. Annual sums must reconcile with national daily sums for the same country/year. Land and borders come from public-domain Natural Earth through `world-atlas`.

Nulls are missing/unknown, not zero. Synthetic label visible throughout. Web should gracefully handle empty datasets and disabled rhythm without inventing results. A complete statistics week has seven unique observed dates; the final partial January-1-based week remains inspectable but does not enter seasonal or anomaly statistics.

## Share links

Annual country grids can share a geometric center at borders. The rendered layer resolves these to one square: the selected country takes priority, with a stable country/ID ordering elsewhere. Resolution occurs before filtering unknown values, so a selected-country null cannot silently show a neighbor's number. The selected card identifies its own country and source. The underlying country-specific scientific records are unchanged.

Versioned query parameters restore the published region, date range, selected daily cell, page, raw/harmonized scale and optional evidence week. The globe year follows the end date. Region and cell identifiers are checked against published allowlists; malformed or unavailable values recover with visible notices. Links use the current data publication and are not immutable snapshots. Camera position, annual globe-cell selection and Earth/table preference are not persisted. Clipboard failure exposes a selectable URL.

## Scope decisions
Use 3 parallel agents plus coordinator due available concurrency (six workstreams consolidated). Shared checkout with disjoint file ownership avoids merge races; do not change branches or commit while others write. Coordinator commits integrated result. Record deviations in DECISIONS.md.
