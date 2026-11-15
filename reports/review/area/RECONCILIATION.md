# Area cells: reconciliation with the published national series

Data: REAL FIRMS DATA. The area cells are a display feature: national calibration is used, and local accuracy has not been validated.
Script: `python -m pipeline.area_cells count ...` then `python -m pipeline.area_cells build` (table: `reconciliation.csv`).

## Method

Every 0.25-degree cell gets a monthly Aqua-reference-equivalent series from the frozen model, with no refitting:
- observed Aqua for 2003-2012;
- converted S-NPP VIIRS for 2013-2024, using each country's saved selection (B1 for Australia, Brazil and the United States; M1 for Bangladesh, Egypt, India and Nepal) and the saved ratios.

Cleaning is the official `pipeline.clean.clean_frame`. Summed over all cells, each month should equal the published national monthly series (`web/public/data/{country}.json`), because the conversion is linear in counts. Months marked "no observation" are excluded from the comparison and are not cell values.

## Result (257 comparable months per country)

| Country | Model | Max relative difference | Month of max | Whole-record difference |
|---|---|---:|---|---:|
| Australia | B1 | 0.43% | 2013-01 | -0.002% |
| Bangladesh | M1 | 0.008% | 2020-07 | 0.000% |
| Brazil | B1 | 0.000003% | 2015-03 | 0.000% |
| Egypt | M1 | 0.56% | 2013-01 | -0.0007% |
| India | M1 | 0.036% | 2013-01 | 0.000% |
| Nepal | M1 | 0.062% | 2013-01 | -0.0002% |
| United States | B1 | 0.000005% | 2024-01 | 0.000% |

All remaining differences are below 0.6%, and every difference above rounding falls in January 2013. That is the first converted month. Converting UTC to local time moves some 31 December 2012 UTC detections into 1 January 2013 local time. Those detections sit in the 2012 VIIRS archive, which is not on this machine. The published national series had that file.

## Output

| Country | Cells with detections | File size |
|---|---:|---:|
| Australia | 10,562 | 2.10 MiB |
| Bangladesh | 233 | 0.04 MiB |
| Brazil | 11,001 | 4.74 MiB |
| Egypt | 349 | 0.05 MiB |
| India | 4,545 | 1.36 MiB |
| Nepal | 252 | 0.07 MiB |
| United States | 14,794 | 2.84 MiB |

Each file is under 25 MiB, and the seven files total 11.2 MiB. They are loaded only when a user opens the area tool for a country.
