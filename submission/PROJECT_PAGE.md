# FIRETRACE

**Challenge:** Harmonization of MODIS and VIIRS Hot Spots

**Team:** Bhaktapur, Nepal

## Act 1: Did fire activity change, or did our camera change?

VIIRS (from 2012) detects smaller fires than MODIS, so a naively joined record can jump. FIRETRACE builds an Aqua-reference-equivalent detection record with explicit comparison limits.

Terra, Aqua and VIIRS are never pooled. We compare three models: uncalibrated VIIRS (B0), one training ratio (B1) and ratios by country, day/night and fire intensity (M1). We trained on 2013-2017, chose models on 2018-2019 and tested once on 2020-2024. Nepal's M1 weekly test error is 11.3 versus 43.3 for B1. In the US the simpler B1 wins. Egypt keeps a +52% bias, and the US fit weakens through the test years.

The historical calendar covers Australia, Bangladesh, Brazil, Egypt, India, Nepal and the United States, 2003-2024: raw/harmonized toggle, typical seasons, unusual weeks, evidence cards and CSV/ICS downloads. It complements near-real-time alerts such as ICIMOD's; it is not a forecast. Hotspots are detections, not a count of fires.

## Act 2: A separately measured weekly pattern

We reproduce a known weekly pattern in each satellite record separately. Independently, FIRETRACE tests whether its historical calendar survives a change of sensor and calibration.

We fixed rest days (Sunday: US, Australia, Brazil, India; Saturday: Nepal; Friday: Bangladesh, Egypt) and a rule: the US replicates the known Sunday dip, and at least two other countries have their rest day lowest and significant after correction in two of three streams.

**Sunday dip clear in the US and Australia, weaker in Brazil, and not established by the country rule where the rest day is Friday or Saturday. Our pre-specified rule passed narrowly; a stricter version fails on Brazil on the 2002-2024 record.**

The US (3 of 3 streams, Sunday 22-33% below an average day) and Australia (3 of 3) pass. Brazil passes two streams, not VIIRS; its Terra industrial-source control dips only in 2002-2007. All three passing countries rest on Sunday: the result does not follow different national rest days. Nepal's country rule has low power for a modest Saturday dip.

Exploratory one-degree map: northeast India has 19 of 26 significant cells (14 of 21 mostly inside India); Aqua agrees. The deepest dips are in Nagaland, Mizoram and Manipur, where Sunday detections fall to about 40% of an average day. No weekly dip is established in the rest of India, including Punjab. Causes remain unresolved; a failed rest-day test does not classify fire causes.

[Live application](https://firetrace-bhaktapur-2026.pages.dev/) · [Source repository](https://github.com/Water-Mal0ne/FIRETRACE)

[NASA data: FIRMS](https://firms.modaps.eosdis.nasa.gov/country/) · [Weekly-cycle research context](https://doi.org/10.1002/2015GL066383)

**AI disclosure:** Codex and Claude Code assisted; see `AI_DISCLOSURE.md`. MIT licensed.

**NASA does not endorse this project.**
