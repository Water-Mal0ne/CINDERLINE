# FIRETRACE

**Challenge:** Harmonization of MODIS and VIIRS Hot Spots

**Team:** Bhaktapur, Nepal

**Status:** Seven-country submission draft; consult `DEPLOYMENT.md` for the verified live revision.

## Did fire activity change—or did our camera change?

A satellite fire record can mix environmental change with changes in what the instrument detects. FIRETRACE makes that comparison inspectable for fire and land managers using NASA FIRMS observations.

Our signature is an evidence journey: choose one observed week, compare separate instrument counts, inspect its Aqua-equivalent estimate and calibration bounds, check held-out validation, then share a link that reopens the same evidence. Terra, Aqua and VIIRS are never pooled into a fictitious sensor. Hotspots remain detections, not independent fires.

The working calendar connects historical activity to typical seasons, high-activity windows, unusual-period flags and CSV/ICS exports. A rotatable Earth displays 41,986 annual grid cells on one fixed reference scale. National totals use every qualifying cell; 12 training-selected daily cells per country support detailed inspection.

**Supported scope:** Australia, Bangladesh, Brazil, Egypt, India, Nepal and the United States, 2003–2024. The release processes 273 verified archives and 67.9 million cleaned detections. It uses observed Aqua through 2012 and converted VIIRS thereafter; it does not claim a validated pre-Aqua reconstruction or worldwide coverage.

**Evaluation:** Training is 2013–2017, model selection is 2018–2019, and held-out testing is 2020–2024. All baselines remain visible. Nepal's selected M1 has monthly test MAE 30.24 versus B1 182.52. The US selects simpler B1: MAE 1,537.79 versus M1 2,078.57. Egypt still has +51.68% selected-model bias. These measure agreement with archived Aqua, not ground truth. Adding countries changed the training ratio, so this is a declared seven-country model revision.

Our optional weekly-rhythm study stays disabled: the overall gate is **insufficient_data**. The US and Australia qualify, but Brazil's matching control is flagged, leaving too few qualified countries. We retain the negative/inconclusive evidence rather than weaken the gate. Weekly association cannot establish ignition cause.

A separate grid-sensitivity check exposes substantial local error despite favorable national metrics. Early Terra-bridge feasibility does not yet qualify a reconstruction.

Every displayed value is reproducible. Independent checks verified exact count reduction, held-out selection discipline and lossless decoding of all 731,276 published daily records. Unknown satellite/cloud coverage remains visible. Historical windows and anomaly flags are not forecasts or emergency alerts.

[Live application](https://firetrace-bhaktapur-2026.pages.dev/) · [Source repository](https://github.com/Water-Mal0ne/FIRETRACE), private at the team's request; arrange judge access before submission.

[NASA data: FIRMS](https://firms.modaps.eosdis.nasa.gov/country/) · [Challenge scope guidance](https://github.com/nasa/spaceapps/discussions/2016) · [Weekly-cycle research context](https://doi.org/10.1002/2015GL066383)

**AI disclosure:** Codex assisted with code, tests, review and documentation; see `AI_DISCLOSURE.md`. Synthetic examples are visibly labeled and separate. Software is MIT licensed.

**NASA does not endorse this project.**
