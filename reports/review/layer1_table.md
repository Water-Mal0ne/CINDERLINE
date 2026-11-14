# Layer 1 results: held-out test years 2020-2024, weekly

Data: REAL FIRMS DATA. Source: `reports/harmonization_eval.csv` (official locked evaluation, split=test, aggregation=weekly, pandas W-MON weeks), selection from `reports/harmonization_model.json`. Models were selected on 2018-2019 validation daily MAE before the test years were evaluated; B0 has no fitted parameter and was never a candidate. Units: Aqua-reference-equivalent detections per week; bias is (sum of model - sum of Aqua) / sum of Aqua over the test weeks.

| Country | Model | Selected | Validation daily MAE | Test bias (%) | Test weekly MAE | Test weekly r |
|---|---|---|---:|---:|---:|---:|
| Australia | B0 |  |  | +665.7 | 15,767.9 | 0.962 |
| Australia | B1 | **yes** | 134.19 | +11.0 | 514.9 | 0.962 |
| Australia | M1 |  | 173.40 | -2.6 | 776.1 | 0.925 |
| Bangladesh | B0 |  |  | +357.1 | 127.1 | 0.926 |
| Bangladesh | B1 |  | 4.28 | -33.7 | 18.3 | 0.926 |
| Bangladesh | M1 | **yes** | 4.27 | +6.8 | 12.1 | 0.921 |
| Brazil | B0 |  |  | +517.3 | 22,343.7 | 0.979 |
| Brazil | B1 | **yes** | 119.43 | -10.5 | 694.3 | 0.979 |
| Brazil | M1 |  | 122.67 | +5.4 | 950.2 | 0.975 |
| Egypt | B0 |  |  | +3135.7 | 175.8 | 0.790 |
| Egypt | B1 |  | 3.09 | +369.2 | 20.7 | 0.790 |
| Egypt | M1 | **yes** | 0.87 | +51.7 | 4.3 | 0.729 |
| India | B0 |  |  | +702.1 | 7,183.9 | 0.903 |
| India | B1 |  | 82.49 | +16.3 | 377.4 | 0.903 |
| India | M1 | **yes** | 70.92 | -2.4 | 337.9 | 0.930 |
| Nepal | B0 |  |  | +1167.2 | 566.7 | 0.966 |
| Nepal | B1 |  | 6.16 | +83.8 | 43.3 | 0.966 |
| Nepal | M1 | **yes** | 3.73 | -8.1 | 11.3 | 0.977 |
| United States | B0 |  |  | +601.4 | 7,298.4 | 0.905 |
| United States | B1 | **yes** | 57.43 | +1.7 | 390.8 | 0.905 |
| United States | M1 |  | 69.37 | +12.9 | 514.8 | 0.884 |
