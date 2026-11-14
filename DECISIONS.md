# Implementation decisions

## Scope and execution
- Consolidated six requested workstreams into three parallel agents plus the coordinator, matching the available concurrency limit. Used disjoint file ownership in one new repository instead of simultaneous branch switches.
- Built the specified Python analysis plus Vite/React/TypeScript static app. No chatbot, forecasts, 3D globe or unvalidated classifier.
- The first integrated release targets Nepal and the United States, using real NASA FIRMS archives. Other regions remain supported by download/analysis configuration and are not falsely advertised as analyzed.
- The initial archive request is 2012–2025. The release does not claim a validated 2000-present reconstruction or an implemented Terra-to-Aqua historical bridge. Extending earlier requires separate validation.
- The initial model exports 12 cells per country selected by training-period activity; the web exporter has an additional 96-cell upper limit. Country totals use all analyzed cells. The UI discloses the displayed-cell limit; it is not a complete arbitrary-area analysis tool.

## Scientific interpretation
- A disappearing 2012 jump is not a criterion. Model choice uses validation years; test years are evaluated after selection, and a simpler model may win.
- Every number carries an instrument/reference interpretation. Counts are satellite detections, not independent fires or burned area.
- A downloaded complete annual archive establishes input-file provenance, not cloud-free satellite observation coverage. Unknown coverage remains explicit.
- Weekday patterns are association evidence. Sensors observe overlapping events; agreement is corroboration, not independent replication.
- Negative controls are diagnostic; industrial activity can itself have a weekly rhythm. No significant control result is not proof of equivalence or absence of bias.
- The code may correct reference-script problems. It preserves the intended scientific questions, not known implementation defects.
- Synthetic fixtures and results are kept separate. They cannot activate the production rhythm module.
- Historical anomaly calculations exclude the target year from the comparison history. Calendar bins are January-1-anchored seven-day periods, not ISO week numbers; bin 53 is short.
- Critical-period ICS exports describe historical seasonality, never a prediction or emergency warning.

## Publication
- Uses a private Sites deployment for the initial preview. Private publication does not make it accessible to judges; public sharing or alternate hosting is a separate audience decision.
- Raw archives, caches, secrets, dependency folders and the Python environment are excluded from Git. Download manifests and reproducible analysis code are included.
