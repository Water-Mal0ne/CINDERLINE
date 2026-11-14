# FIRETRACE

**Challenge:** Harmonization of MODIS and VIIRS Hot Spots

**Team:** Bhaktapur, Nepal

## Act 1: Did fire activity change, or did our camera change?

VIIRS (from 2012) sees many more small fires than MODIS, so a naively joined record jumps. FIRETRACE puts both on one scale, MODIS-Aqua-equivalent detections, so years compare fairly.

Terra, Aqua and VIIRS are never pooled. We compare three models: uncalibrated VIIRS (B0), one training ratio (B1) and ratios by country, day/night and fire intensity (M1). We trained on 2013-2017, chose models on 2018-2019 and tested once on 2020-2024. Nepal's M1 monthly test error is 30.24 versus 182.52 for B1. In the US the simpler B1 wins. Egypt keeps a +51.68% bias.

The burning activity calendar covers Australia, Bangladesh, Brazil, Egypt, India, Nepal and the United States, 2003-2024: raw versus harmonized toggle, typical seasons, unusual weeks, evidence cards and CSV/ICS downloads. Hotspots are detections, not a count of fires.

## Act 2: Is there a human rhythm in the record?

Nature has no seven-day cycle; people do. Before looking at the data we fixed each country's rest day (Sunday for the US, Australia, Brazil and India; Saturday for Nepal; Friday for Bangladesh and Egypt) and a pass rule: the US replicates the known Sunday dip, and at least two other countries show their rest day as the lowest weekday, significant after correction, in two of three satellite streams.

**Result: pass.** The US (3 of 3 streams, Sunday 22-33% below an average day), Australia (3 of 3) and Brazil (2 of 3) pass. India, Nepal, Bangladesh and Egypt do not. US and Australian static-source controls are clean.

All three passing countries rest on Sunday; Friday- and Saturday-rest countries did not show a dip, so this does not show the dip following each country's own rest day. Brazil's Terra static-source control also dips on Sunday, so Brazil's support is weaker than the US and Australia.

An exploratory one-degree map: in northeast India 19 of 26 cells are significant (14 of 21 cells mostly inside India) and Aqua agrees; the rest of India shows none.

Within India, the Sunday dip is concentrated in the northeastern hill states, deepest in Nagaland, Mizoram and Manipur, where Sunday detections fall to about 40% of an average day; the rest of India, including the Punjab crop-burning belt, shows no weekly dip. The cause is unresolved; local scheduling of burning is one possible explanation we have not tested.

A dip is consistent with people scheduling their burning. It does not prove who lit a fire, and no dip does not mean fires are weather-driven.

[Live application](https://firetrace-bhaktapur-2026.pages.dev/) · [Source repository](https://github.com/Water-Mal0ne/FIRETRACE)

[NASA data: FIRMS](https://firms.modaps.eosdis.nasa.gov/country/) · [Weekly-cycle research context](https://doi.org/10.1002/2015GL066383)

**AI disclosure:** Codex and Claude Code assisted; see `AI_DISCLOSURE.md`. MIT licensed.

**NASA does not endorse this project.**
