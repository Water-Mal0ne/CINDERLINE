# FIRETRACE

**Challenge:** Harmonization of MODIS and VIIRS Hot Spots

**Team:** Bhaktapur, Nepal

**Status:** Seven-country submission draft; check `DEPLOYMENT.md` for the verified live revision.

## Act 1: Did fire activity change, or did our camera change?

When VIIRS joined MODIS in 2012, satellites started seeing many more small fires. Join the records naively and fire activity seems to jump. FIRETRACE puts both on one named scale, MODIS-Aqua-equivalent detections, so fire and land managers can compare years fairly.

Terra, Aqua and VIIRS are never pooled. We compare three models: uncalibrated VIIRS (B0), one training ratio (B1) and ratios by country, day/night and fire intensity (M1). We trained on 2013-2017, chose models on 2018-2019 and tested once on 2020-2024. Nepal's M1 has a monthly test error of 30.24 versus 182.52 for B1. In the US the simpler B1 wins (1,537.79 versus 2,078.57). Egypt keeps a +51.68% bias, and we show it.

The burning activity calendar covers Australia, Bangladesh, Brazil, Egypt, India, Nepal and the United States, 2003-2024: raw versus harmonized toggle, typical season, high-activity windows, unusual weeks, evidence cards and CSV/ICS downloads. Any week opens to its separate sensor counts, conversion and uncertainty, and a share link reopens it. Hotspots are detections, not a count of fires.

## Act 2: Is there a human rhythm in the record?

Nature has no seven-day cycle; people do. Before looking at the data we fixed each country's rest day (Sunday for the US, Australia, Brazil and India; Saturday for Nepal; Friday for Bangladesh and Egypt) and a pass rule: the US must replicate the known Sunday dip, and at least two other countries must show their rest day as the lowest weekday, significant after correction, in at least two of the three satellite streams.

**Result: pass.** The US (3 of 3 streams, Sunday 22-33% below an average day), Australia (3 of 3) and Brazil (2 of 3) pass. India, Nepal, Bangladesh and Egypt do not. Static heat sources show no such pattern in the US and Australia.

Two caveats are part of the result. All three passing countries rest on Sunday; Friday- and Saturday-rest countries did not show a dip, so this does not show the dip following each country's own rest day. And Brazil's Terra static-source control also dips on Sunday, so Brazil's support is weaker than the US and Australia.

An exploratory map of one-degree cells shows where the dip is. In India it sits almost entirely in the northeast: 19 of 26 cells there are significant, Aqua agrees, and the rest of India shows no dip.

[PLACEHOLDER: team explanation of the northeast India pattern, to be written and reviewed before submission.]

A dip is consistent with people scheduling their burning. It does not prove who lit a fire, and no dip does not mean fires are weather-driven.

[Live application](https://firetrace-bhaktapur-2026.pages.dev/) · [Source repository](https://github.com/Water-Mal0ne/FIRETRACE)

[NASA data: FIRMS](https://firms.modaps.eosdis.nasa.gov/country/) · [Weekly-cycle research context](https://doi.org/10.1002/2015GL066383)

**AI disclosure:** Codex and Claude Code assisted with code, tests, analysis and documentation; see `AI_DISCLOSURE.md`. Software is MIT licensed.

**NASA does not endorse this project.**
