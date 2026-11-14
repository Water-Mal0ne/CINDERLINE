# FIRETRACE

**Challenge:** Harmonization of MODIS and VIIRS Hot Spots

**Team:** Bhaktapur, Nepal

## Act 1: Did fire activity change, or did our camera change?

VIIRS (from 2012) sees many more small fires than MODIS, so a naively joined record jumps. FIRETRACE builds an Aqua-reference-equivalent detection record, so years compare fairly.

Terra, Aqua and VIIRS are never pooled. We compare three models: uncalibrated VIIRS (B0), one training ratio (B1) and ratios by country, day/night and fire intensity (M1). We trained on 2013-2017, chose models on 2018-2019 and tested once on 2020-2024. Nepal's M1 weekly test error is 11.3 versus 43.3 for B1. In the US the simpler B1 wins. Egypt keeps a +52% bias, and the US fit weakens through the test years.

The burning activity calendar is historical and descriptive. It covers Australia, Bangladesh, Brazil, Egypt, India, Nepal and the United States, 2003-2024: raw versus harmonized toggle, typical seasons, unusual weeks, evidence cards and CSV/ICS downloads. It is a long-term historical calendar, complementary to near-real-time fire alert systems such as ICIMOD's, not a replacement. Hotspots are detections, not a count of fires.

## Act 2: Is there a human rhythm in the record?

Nature has no seven-day cycle; people do. We fixed each country's rest day (Sunday for the US, Australia, Brazil and India; Saturday for Nepal; Friday for Bangladesh and Egypt) and a pass rule: the US replicates the known Sunday dip, and at least two other countries show their rest day as the lowest weekday, significant after correction, in two of three satellite streams.

**Sunday dip clear in the US and Australia, weaker in Brazil, and absent where the rest day is Friday or Saturday. Our pre-specified rule passed narrowly; a stricter version fails on Brazil on the 2002-2024 record.**

The US (3 of 3 streams, Sunday 22-33% below an average day) and Australia (3 of 3) pass clearly. Brazil is suggestive: two streams pass, its VIIRS stream does not, and its Terra static-source control also dips on Sunday. All three passing countries rest on Sunday, so this does not show the dip following each country's own rest day. Nepal's data are too sparse to detect a modest Saturday dip.

An exploratory one-degree map: in northeast India 19 of 26 cells are significant (14 of 21 cells mostly inside India) and Aqua agrees. Within India, the Sunday dip is concentrated in the northeastern hill states, deepest in Nagaland, Mizoram and Manipur, where Sunday detections fall to about 40% of an average day; the rest of India, including the Punjab crop-burning belt, shows no weekly dip. The cause is unresolved; local scheduling of burning is one possible explanation we have not tested.

A dip is consistent with people scheduling their burning. It does not prove who lit a fire, and no dip does not mean fires are weather-driven.

[Live application](https://firetrace-bhaktapur-2026.pages.dev/) · [Source repository](https://github.com/Water-Mal0ne/FIRETRACE)

[NASA data: FIRMS](https://firms.modaps.eosdis.nasa.gov/country/) · [Weekly-cycle research context](https://doi.org/10.1002/2015GL066383)

**AI disclosure:** Codex and Claude Code assisted; see `AI_DISCLOSURE.md`. MIT licensed.

**NASA does not endorse this project.**
