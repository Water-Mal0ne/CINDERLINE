# Harmonization evaluation — seven-country-v1

Archive fingerprint: 4bf6e7635b6cb9b7437fb069e4afb4866c5347dd15d46549288686fb8b21edd7

Fit: 2013–2017. Validation choice: 2018–2019 daily MAE. Choices locked before held-out 2020–2024 evaluation.

Global B1 changes because the declared training-country scope expands. The preserved 76-archive baseline matches exactly through the count route.

| Country | Selected | Monthly test MAE | Test bias | Correlation |
|---|---|---:|---:|---:|
| Australia | B1 | 2003.2690 | +11.0370% | 0.9725 |
| Bangladesh | M1 | 23.4645 | +6.7730% | 0.9677 |
| Brazil | B1 | 2282.6144 | -10.4893% | 0.9909 |
| Egypt | M1 | 15.0431 | +51.6755% | 0.8546 |
| India | M1 | 1365.9883 | -2.3840% | 0.9343 |
| Nepal | M1 | 30.2396 | -8.1142% | 0.9954 |
| United_States | B1 | 1537.7908 | +1.7182% | 0.9330 |

Egypt retains substantial held-out positive bias (+51.6755%) despite validation selecting M1. These are archived-detection conversions, not estimates of true fires or burned area.

Weekly statistical replication passes US + Australia + Brazil, but Brazil's matched control is flagged. The final release gate remains insufficient_data and production_allowed is false.
