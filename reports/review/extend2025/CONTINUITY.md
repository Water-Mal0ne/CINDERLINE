# 2025 extension and out-of-sample continuity check

Data: REAL FIRMS DATA, 2025 country archives (S-NPP VIIRS and MODIS, FIRMS files dated 10 October 2026).
Script: `python -m pipeline.extend_2025 count ...` then `build` (table: `continuity_2025.csv`).

## What was added

2025 is added to the calendar as **converted VIIRS, beyond the validation period**. That covers the national series and the 12 published cells per country.
- **Model:** each country's frozen selection and ratios, applied with no refitting.
- **Cleaning:** the official `clean_frame`, with civil time from exact coordinates. The 2024 archives supply the 1 January 2025 local-time spill.
- **Calibration intervals:** not computed for 2025. The fields are left empty, not zero, because the 200-draw interval needs the full training bootstrap, which was not re-run.
- **Unchanged:** the weekly climatology, anomaly flags, critical periods, evaluation and weekly-rhythm results remain based on 2003-2024.

## Gaps and no-observation days

No 2025 day lacks S-NPP VIIRS detections in all seven countries. One partial-day gap was found and marked "no observation": on **12 November 2025**, VIIRS has zero detections in Australia, Bangladesh, Egypt, India and Nepal, while MODIS recorded detections. For example, Australia has Aqua 890, Terra 308, VIIRS 0, and India has Aqua 122, VIIRS 0. Brazil and United States VIIRS are normal that day. 31 December 2025 in the western hemisphere may lack late-evening detections, because no 2026 archive exists yet; that day's coverage text says so.

## Continuity check: converted VIIRS against observed MODIS Aqua, 2025

The check uses weekly (W-MON) totals of national vegetation detections, with no-observation days excluded on both sides. 2025 was never used for fitting, selection or evaluation, so it is out of sample in time. Aqua is a reference, not ground truth.

| Country | Model | 2025 bias | 2025 weekly r | Held-out 2020-2024 bias | 2020-2024 weekly r |
|---|---|---:|---:|---:|---:|
| Australia | B1 | +16.4% | 0.982 | +11.0% | 0.962 |
| Bangladesh | M1 | -6.6% | 0.987 | +6.8% | 0.921 |
| Brazil | B1 | **-21.4%** | 0.962 | -10.5% | 0.979 |
| Egypt | M1 | +50.0% | **0.305** | +51.7% | 0.729 |
| India | M1 | -11.1% | 0.942 | -2.4% | 0.930 |
| Nepal | M1 | **-17.6%** | 0.987 | -8.1% | 0.977 |
| United States | B1 | -7.0% | 0.845 | +1.7% | 0.905 |

## Reading

- **Timing holds up:** weekly correlation stays high (0.94-0.99) in five of seven countries, so converted VIIRS still follows Aqua's week-to-week pattern in 2025.
- **Totals drift:** totals moved further from Aqua than in the held-out years in Brazil (-21%), Nepal (-18%), India (-11%) and the United States (-7%). In those four countries converted VIIRS now reads lower than Aqua; Australia reads higher (+16%).
- **Egypt:** the weekly correlation fell to 0.31. It rests on very few detections (237 Aqua detections in 2025).
- **Cause unknown:** this check cannot separate Aqua's late-mission orbit drift, sensor changes, product changes and real changes in burning.
- **What it means for 2025 users:** 2025 is shown as a continuity extension, not a validated product year, and its country totals carry larger uncertainty than the 2020-2024 evaluation suggests.
