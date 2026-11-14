# Additional scientific validation

These checks do not change the seven-country model, the 2020–2024 test evaluation, or the supported 2003–2024 product history.

## Prespecified design

The protocol was saved before calculation. Grid sensitivity freezes the released ratios and country choices, selects 12 coarse cells per country from 2013–2017 vegetation activity, and compares those cells with their four 0.25° children on 2018–2019. Both grids cover exactly the same selected geography; this is a selected-cell sensitivity check, not a claim for every cell.

This grid diagnostic reuses the 2018–2019 block that originally selected each country model. It is not an independent confirmation or a new untouched test. Training activity sums vegetation detections across the separate streams; the selected 0.5° footprints and their four children are clipped to records in each country archive.

The bridge fits one Terra-to-Aqua ratio per country from 2003–2007 and validates on the separate 2008–2011 year block. The unscaled Terra baseline is reported too. The 200 resamples draw entire training years. No candidate or acceptance threshold was chosen after observing validation, and no 2020–2024 data enter either new check.

## Grid sensitivity

| Country | 0.25° normalized monthly absolute error | 0.5° normalized monthly absolute error | 0.25° activity Jaccard | 0.5° activity Jaccard |
| --- | ---: | ---: | ---: | ---: |
| Australia | 31.75% | 23.11% | 0.446 | 0.561 |
| Bangladesh | 35.43% | 29.81% | 0.309 | 0.345 |
| Brazil | 26.01% | 19.47% | 0.363 | 0.439 |
| Egypt | 178.77% | 145.25% | 0.014 | 0.023 |
| India | 34.51% | 32.25% | 0.390 | 0.427 |
| Nepal | 42.71% | 30.75% | 0.210 | 0.282 |
| United States | 145.94% | 144.35% | 0.123 | 0.219 |

Normalized absolute error sums absolute cell-month error over observed Aqua counts across the same geography. Coarsening can cancel local positive/negative errors and merge different within-cell detections; lower error or higher recorded-activity Jaccard is therefore partly an aggregation effect. It does not establish more accurate fire locations, independent truth, or spatial robustness. The full CSV also reports bias, raw per-cell MAE and peak timing. Grid choice remains 0.25°; it was not retuned from these results.

National totals were invariant for every country and each 2013–2019 year up to floating-point summation noise. That is expected because the conversion weights depend on country and sensor strata, not cell identity. It is an arithmetic property, not an independent validation result.

## Early Terra bridge feasibility

| Country | Training Aqua/Terra ratio | Unscaled monthly MAE | Converted monthly MAE | Converted validation bias | Mean peak-week error |
| --- | ---: | ---: | ---: | ---: | ---: |
| Australia | 1.2999 | 3180.25 | 2980.78 | -6.03% | 3.00 |
| Bangladesh | 10.1709 | 203.44 | 139.42 | -1.86% | 1.75 |
| Brazil | 1.9848 | 8493.38 | 3719.68 | +8.21% | 0.50 |
| Egypt | 0.7609 | 20.58 | 19.04 | -8.05% | 2.00 |
| India | 2.9015 | 2687.79 | 1863.82 | +13.63% | 14.50 |
| Nepal | 1.8855 | 75.77 | 32.55 | +1.61% | 0.75 |
| United States | 1.0915 | 1139.54 | 1066.71 | -10.34% | 4.00 |

A positive constant ratio cannot change Terra's peak timing. Differences in overpass time and unmeasured observation conditions remain; a lower count error is not evidence that the instruments observed identical fires. Whole-year bootstrap bounds describe uncertainty in the fitted ratio, not the additional uncertainty of historical reconstruction.

Observed Aqua lay inside the ratio-only 95% calibration interval in the following fractions of active validation months: Australia 8.3%; Bangladesh 22.2%; Brazil 12.5%; Egypt 8.3%; India 10.4%; Nepal 20.0%; United States 10.4%. These are descriptive inclusion rates, not confidence-interval coverage guarantees.

No 2001–2002 reconstruction is published. This feasibility test documents whether a simple bridge improves count agreement; it does not qualify wider total-uncertainty bands or validate transfer to the pre-Aqua period. The supported record remains 2003–2024. A future bridge needs an explicit reconstruction/uncertainty validation protocol before release.

## Reproduction and scope

Archive manifest fingerprint: `4bf6e7635b6cb9b7437fb069e4afb4866c5347dd15d46549288686fb8b21edd7`. `protocol.json` binds the saved model SHA256 and experimental years. Raw observations are never expanded from counts. Archive-complete zero means no qualifying archived detections, not known cloud-free absence of fire; satellite observation coverage is unknown.

Run `python -m pipeline.validation.science_checks --help` for the three preparation paths, three analysis paths, locked model and fresh output directory. The original model and lock are read-only. All output is separate from production model/evaluation files.
