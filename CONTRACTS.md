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

## Web JSON
`web/public/data/index.json`: {label: string, regions: [{id: 'Nepal', name: 'Nepal', file: 'Nepal.json'}], generated_at: ISO, limitations: string[]}.
`web/public/data/{region}.json`: {meta: {region, name, label, period_start, period_end, reference:'MODIS Aqua', model, coverage_note, sources: [{name,url}], centroid:[lon,lat]}, daily:[{date,cell_id:'ALL',raw_terra,raw_aqua,raw_viirs,raw, harmonized,lo,hi,coverage,source,model}], weekly_climatology:[{week,median,p10,p90,critical}], anomalies:[{date,week,value,z_score,status}], critical_periods:[{start_week,end_week,label}], rhythm:null|{gate,streams,rest_day}, eval:[{model,region,split,aggregation,bias_pct,mae,correlation,peak_week_error}], cells:[{id,lat,lon,daily:[same daily]}]}.
Nulls are missing/unknown, not zero. Synthetic label visible throughout. Web should gracefully handle empty datasets and disabled rhythm without inventing results.

## Scope decisions
Use 3 parallel agents plus coordinator due available concurrency (six workstreams consolidated). Shared checkout with disjoint file ownership avoids merge races; do not change branches or commit while others write. Coordinator commits integrated result. Record deviations in DECISIONS.md.
