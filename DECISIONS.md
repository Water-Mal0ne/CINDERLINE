# Implementation decisions

## Scope and execution
- Consolidated six requested workstreams into three parallel agents plus the coordinator, matching the available concurrency limit. Used disjoint file ownership in one new repository instead of simultaneous branch switches.
- Built the specified Python analysis plus Vite/React/TypeScript static app. No chatbot, forecasts or unvalidated classifier. The user subsequently explicitly requested a proper 3D globe heatmap; that instruction overrides the earlier brief's no-3D preference.
- The first integrated release targets Nepal and the United States, using real NASA FIRMS archives. Other regions remain supported by download/analysis configuration and are not falsely advertised as analyzed.
- The initial archive request was 2012–2025. Phase 2 added MODIS 2002–2011 for Nepal/US, giving a 76-archive analyzed snapshot and 10,142,672 cleaned records. Complete displayed local years are 2003–2024: observed Aqua in 2003–2012, converted VIIRS in 2013–2024. No Terra-to-Aqua bridge or 2000-present reconstruction is claimed.
- Daily drill-down exports 12 cells per country selected by training-period activity; the web exporter retains an additional 96-cell upper limit. Country totals use all analyzed cells. Daily cell data are loaded lazily from separate payloads. The new annual 3D globe includes all 15,118 contributing vegetation-detection cells across the supported Nepal/US record; it is not limited to the daily sample and is not worldwide coverage.
- The user deferred worldwide expansion in favor of 3D rendering. Completed extra downloads are preserved but not integrated into the analyzed cache. Explicit cache reuse binds results to the manifest saved with the Parquet; a newer raw-folder manifest must not be substituted. Analysis reuse checks the input/analysis signature before accepting earlier outputs.
- The globe uses exact 0.25-degree grid centers and annual sums calculated with the existing selected model and ratios. It uses a fixed all-year logarithmic color scale rather than rescaling each year. Zero recorded detections, missing values and unprocessed geography remain distinct.
- Natural Earth land and country outlines, redistributed through world-atlas 2.0.2, provide the globe's geographic context. They are not FIRMS measurements or observation-coverage masks.

## Scientific interpretation
- A disappearing 2012 jump is not a criterion. Model choice uses validation years; test years are evaluated after selection, and a simpler model may win.
- Every number carries an instrument/reference interpretation. Counts are satellite detections, not independent fires or burned area.
- A downloaded complete annual archive establishes input-file provenance, not cloud-free satellite observation coverage. Unknown coverage remains explicit.
- Weekday patterns are association evidence. Sensors observe overlapping events; agreement is corroboration, not independent replication.
- Negative controls are diagnostic; industrial activity can itself have a weekly rhythm. No significant control result is not proof of equivalence or absence of bias.
- The code may correct reference-script problems. It preserves the intended scientific questions, not known implementation defects.
- Synthetic fixtures and results are kept separate. They cannot activate the production rhythm module.
- Historical anomaly calculations exclude the target year from the comparison history. Calendar bins are January-1-anchored seven-day periods, not ISO week numbers. Climatology and anomaly comparisons require complete bins 1–52; short bin 53 and other partial bins are excluded, while the underlying daily observations remain available.
- Historical extension preserves the 2013–2017 calibration, 2018–2019 selection and 2020–2024 evaluation windows, along with the selected models and reported test results. No model was chosen or retuned using the test set to accommodate the early record.
- Display raw values follow archive eligibility: Aqua before eligible VIIRS, then VIIRS. The actual transition is 2013 for this snapshot. A hardcoded 2012 switch must not manufacture a missing baseline or a required discontinuity.
- Equal conversion bounds on observed Aqua mean identity/no conversion, not perfect measurement certainty. Converted-VIIRS bounds remain calibration-only bootstrap intervals.
- Critical-period ICS exports describe historical seasonality, never a prediction or emergency warning.

## Publication
- The initial preview used private Sites hosting. At the user's request the live application is now public on free Cloudflare Pages. The user requested a new GitHub repository named FIRETRACE with private visibility; source publication is separate from the public application.
- Raw archives, caches, secrets, dependency folders and the Python environment are excluded from Git. Download manifests and reproducible analysis code are included.
