# Season preservation under common outage masks

The original retrospective comparison is reproduced without fitting or selecting a model. The same retained local dates are used for Aqua and every VIIRS alternative. The primary mask removes 73 excluded dates from documented outages and previously flagged common zero-detection days; the padded sensitivity removes 87 dates after expanding each interval by one day at both ends.

## Does the original India/Nepal example survive?

The comparison below is **B1 versus the frozen selected M1**, using the separate whole-year replacement control, averaged equally across 2020–2024. TV × 100 is monthly-pattern disagreement in points, not a percentage of actual fires. Annual error × 100 is absolute relative count disagreement with Aqua on retained dates; masked totals are not complete calendar-year totals.

| Country | Calendar | B1 annual error (%) | Selected annual error (%) | B1 TV (points) | Selected TV (points) |
|---|---|---:|---:|---:|---:|
| India | unmasked | 16.4560 | 3.8013 | 13.5870 | 16.2943 |
| India | primary | 13.8349 | 4.0537 | 12.3145 | 15.5725 |
| India | padded | 13.9448 | 4.5146 | 12.2786 | 15.4238 |
| Nepal | unmasked | 83.3402 | 7.9085 | 14.5530 | 4.5109 |
| Nepal | primary | 77.6713 | 8.3035 | 13.8237 | 5.7534 |
| Nepal | padded | 76.7405 | 8.0578 | 13.7869 | 5.6902 |

India's better-total / worse-monthly-shape direction survives both masks: **True**. Nepal's lower monthly TV direction survives both masks: **True**. These are descriptive direction checks, not new significance tests or a claim that every year/cut improves.

## All countries and within-year scenarios

February–December cuts remain the primary artificial handover scenarios. Each country contributes 55 dependent cuts per calendar. Raw, B1 and selected outputs and all year-level outcomes are retained; January whole-year and next-January no-handover controls stay separate.

| Country | Mask | Raw TV | B1 TV | Selected TV | Selected better / tied / worse vs B1 |
|---|---|---:|---:|---:|---|
| Australia | unmasked | 29.1316 | 5.7327 | 5.7327 | 0 / 55 / 0 |
| Australia | primary | 28.9217 | 4.9020 | 4.9020 | 0 / 55 / 0 |
| Australia | padded | 29.0877 | 5.0789 | 5.0789 | 0 / 55 / 0 |
| Bangladesh | unmasked | 19.4412 | 4.1529 | 3.1350 | 32 / 0 / 23 |
| Bangladesh | primary | 19.6277 | 4.7417 | 2.4939 | 36 / 0 / 19 |
| Bangladesh | padded | 19.9500 | 4.7782 | 2.5225 | 36 / 0 / 19 |
| Brazil | unmasked | 16.2355 | 3.3516 | 3.3516 | 0 / 55 / 0 |
| Brazil | primary | 15.5745 | 2.5950 | 2.5950 | 0 / 55 / 0 |
| Brazil | padded | 15.5012 | 2.4823 | 2.4823 | 0 / 55 / 0 |
| Egypt | unmasked | 37.6896 | 23.5071 | 11.6989 | 50 / 0 / 5 |
| Egypt | primary | 37.4739 | 23.2850 | 11.4083 | 48 / 0 / 7 |
| Egypt | padded | 37.4127 | 23.2342 | 11.4015 | 47 / 0 / 8 |
| India | unmasked | 34.8105 | 7.4235 | 10.6515 | 8 / 0 / 47 |
| India | primary | 34.6181 | 6.9586 | 10.3705 | 5 / 0 / 50 |
| India | padded | 34.7142 | 6.8048 | 10.2062 | 5 / 0 / 50 |
| Nepal | unmasked | 27.0446 | 5.6692 | 2.0456 | 24 / 0 / 31 |
| Nepal | primary | 26.8809 | 5.4749 | 2.3716 | 24 / 0 / 31 |
| Nepal | padded | 26.9437 | 5.4747 | 2.3563 | 24 / 0 / 31 |
| United_States | unmasked | 28.1014 | 7.0233 | 7.0233 | 0 / 55 / 0 |
| United_States | primary | 28.4034 | 6.7401 | 6.7401 | 0 / 55 / 0 |
| United_States | padded | 28.5039 | 6.7621 | 6.7621 | 0 / 55 / 0 |

All TV entries above are disagreement points (TV × 100). Australia, Brazil and the United States retain B1; their selected outputs must coincide with B1.

## Coverage and limitations

All 35 country-years retain every month under both masks. The minimum retained month has 12 dates. The output includes 4,095 scenario rows across the original and two masked calendars, including all controls. A zero-recorded-count retained day stays zero; an excluded date contributes to neither series. If any month had no retained dates, TV and peak agreement would be explicitly undefined rather than zero.

- The experiment is retrospective: these 2020–2024 years were already examined. It is not a new holdout, independent preregistration, or a validation of actual fires.
- Aqua is the observation reference, not ground truth. Satellite sensitivity, cloud cover, overpass timing and remaining processing gaps can affect both streams.
- Exact outage labels are interpreted as local dates, while source notices may use UTC. One-day padding tests that boundary choice; it does not certify complete observation exposure.
- The mask includes 38 VIIRS dates (33 documented and five previously flagged common zero dates) and 35 Aqua dates. It is a common union applied to every country and alternative, not an effect-selected mask.
- Monthly shares use observed sums on retained days, with no extrapolation or new rate normalization. A shared mask improves comparability but can remove seasonal information unevenly.
- Cuts reuse the same data; no p-values or independent-trial claims are made. Passing a mean direction does not imply improvement for every cut, year, metric or country.
- Source support is the preserved, already reconciled national sufficient-statistics dataset. This rerun does not download/re-clean raw archives or refit official ratios, gates or model selection.

## Reproduce and inspect

```sh
python -m pipeline.review.season_check
python scripts/verify_season_check.py
```

`source_snapshot.json` pins original inputs; `input_manifest.json` records current hashes. `original_scenarios.csv`, `original_all_country_whole_year_comparison.csv` and `original_protocol.md` preserve the unmasked baseline. `frozen_outage_dates.csv` is the exact prior 73/87-date record. `scenarios.csv`, `whole_year_comparison.csv`, `country_summary.csv`, `year_summary.csv`, `monthly_coverage.csv`, `excluded_dates.csv`, `summary.json` and `invariant_checks.json` expose the rerun. Independent verification is reported separately; this script does not assert its own independent approval.
