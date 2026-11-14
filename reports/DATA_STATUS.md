# Data and harmonization implementation

- Downloader validates CSV headers, counts rows, records SHA-256 checksums, uses temporary files and atomic replacement, retries failures and writes an incremental manifest.
- Real NASA FIRMS annual archives downloaded for Nepal and the United States, both MODIS and VIIRS S-NPP, 2012–2025: 56 files, 9,401,501 raw records, 749,570,942 bytes. Complete archive transfer does not imply complete satellite observation coverage.
- Cleaning preserves stream identity and static-source controls; invalid timestamps, missing types and unresolved timezones are explicit. Multi-zone countries use exact-coordinate IANA timezone lookup, including historical civil-time offsets.
- Harmonization fits B1 and M1 on 2013–2017, selects by daily validation MAE in 2018–2019 and reports weekly/monthly held-out metrics for 2020–2024. M1 ratios are stratified by country, day/night and reported FRP class, with sparse-stratum shrinkage toward B1.
- Calibration intervals bootstrap training years 200 times. They are not total uncertainty or prediction intervals.
- Public calendar counts refer to archived qualifying detections. Zero is not a statement that an area was observed cloud-free or had no fire.
- Country totals include all cells. Map output contains up to 12 cells selected by training-period activity, per country.
- Supported complete local-year output is 2013–2024 for the initial archives. A pre-Aqua bridge, remaining five countries, alternate-grid sensitivity and M2 are not implemented/validated in this first build.
- Eleven focused data/harmonization tests pass, including mixed-sensor confidence serialization to Parquet and equivalence of vectorized bootstrap predictions to direct ratio sums. A separate synthetic end-to-end check recovers an injected fourfold instrument ratio exactly; synthetic results do not establish real-world accuracy.
- Full cleaned data saved at `data/processed/detections.parquet`: 8,945,662 real records, including vegetation and static-source controls, with manifest and diagnostic attributes.
- A 2.1 MB real Nepal 2019–2021 processed sample is included at `data/sample/detections_Nepal_2019_2021.parquet`; it is a development sample, not enough to fit the prescribed historical model.

Reproduction:

```powershell
.\.venv\Scripts\python.exe -m pipeline.download --countries Nepal United_States --years 2012 2025
.\.venv\Scripts\python.exe -m pytest tests/test_data.py tests/test_harmonize.py -q
```

Use `pipeline.run_all` for integrated exports, evaluation and figures.
