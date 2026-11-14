# Submission draft status

- Project page populated with actual two-country results; remains under 500 words.
- Seven-slide outline drafted, with actual-data and synthetic evidence separated.
- 30-second demonstration script drafted; recording is not produced by this file.
- Current event formatting limits must be verified before submission.
- Metrics populated from `reports/harmonization_eval.csv`, selected models from `harmonization_model.json` and gate from `kill_test_gate.json`: Nepal M1, US B1; history now 2003–2024; unchanged 2020–2024 test results; overall rhythm `insufficient_data`.
- These drafts have not been submitted or sent externally.
- Public Cloudflare Pages deployment verified on November 14, 2026: https://firetrace-bhaktapur-2026.pages.dev/. A public source repository URL remains a submission blocker.
- Rhythm test suite: 8 passed using `.venv\Scripts\python.exe -m pytest tests/test_rhythm.py -q`.
- Methods documentation checked against the current B1/M1 harmonizer: region/daynight/FRP strata, fixed shrinkage, validation daily MAE selection, 200 bootstrap draws, 12 training-selected map cells, no early Terra bridge and no M2.
