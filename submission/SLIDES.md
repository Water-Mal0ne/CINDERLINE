# FIRETRACE: seven-slide presentation outline

Draft. Check the event's actual slide and video requirements before submitting. Two separate analyses: harmonization and the Weekly Rhythm Index. Keep unfavorable results visible.

## 1. The question

**Title:** Did fire activity change, or did our camera change?

Show a real regional record with its instrument labels. When VIIRS joined MODIS in 2012 it saw many more small fires, so a naive joined record appears to jump. A hotspot is a detected pixel, not an independent fire.

**Opening line:** "A sharper satellite can make the fire record change even when burning has not. FIRETRACE builds a historical calendar on a declared reference scale, and tests whether better-looking numbers preserve the season people need to understand."

## 2. Act 1: one comparable history for seven countries

**Title:** A burning activity calendar on one named scale

Select a country in the calendar (Australia, Bangladesh, Brazil, Egypt, India, Nepal, United States; 2003-2024). Flip the raw versus harmonized toggle to compare the record on its original sensor scales and the Aqua reference scale. This comparison does not isolate the cause of a real historical change. Show typical season, high-activity windows and unusual weeks. This is historical context, not a forecast.

## 3. Act 1: the method and the honest test

**Title:** Separate streams, one reference, a locked evaluation

FIRMS archives, local civil dates, Terra/Aqua/VIIRS kept separate, Aqua-reference-equivalent scale. B0 is uncalibrated VIIRS, B1 one training ratio, M1 ratios by country, day/night and fire intensity. Train 2013-2017, select 2018-2019, test once 2020-2024.

| Country | Selected | Selected monthly MAE | Comparator | Remaining limitation |
|---|---|---:|---:|---|
| Nepal | M1 | 30.24 | B1: 182.52 | -8.11% bias |
| United States | B1 | 1,537.79 | M1: 2,078.57 | simpler model wins |
| Egypt | M1 | 15.04 | B1: 90.40 | +51.68% bias |

Units are Aqua-reference-equivalent detections, not fire counts.

## 4. Act 1: one week, back to its evidence

**Title:** Follow the evidence before trusting the trend

Open one week: separate sensor counts, the converted estimate and its bounds, the held-out results, then a share link that reopens the same view.

## 5. Act 2: the separate weekly rhythm test

**Title:** A known weekly pattern, measured separately

We reproduce a known weekly pattern in each satellite record separately. Independently, FIRETRACE tests whether its historical calendar survives a change of sensor and calibration.

Stated rest-day hypotheses: Sunday (US, Australia, Brazil, India), Saturday (Nepal), Friday (Bangladesh, Egypt). Stated pass rule: the US replicates the known Sunday dip, and at least two other countries show their rest day as the lowest weekday, significant after correction, in at least two of three satellite streams.

**Headline:** Sunday dip clear in the US and Australia, weaker in Brazil, and not established by the country rule where the rest day is Friday or Saturday. Our pre-specified rule passed narrowly; a stricter version fails on Brazil on the 2002-2024 record.

**Result: pass.** US 3/3 streams (Sunday 22-33% below an average day), Australia 3/3, Brazil 2/3. India, Nepal, Bangladesh and Egypt fail. Show the Weekly Rhythm Index tab: weekday bars with 95% intervals, rest day highlighted.

## 6. Act 2: what it does and does not show

**Title:** The caveats are part of the result

- All three passing countries rest on Sunday; Friday- and Saturday-rest countries did not pass the country rule, so this does not show the dip following each country's own rest day.
- Brazil's Terra industrial-source control dips on Sunday over 2002-2024, but the dip comes entirely from 2002-2007; over 2013-2024, the window fixed for the rest-day test, the control is flat. Brazil's Sunday dip is weaker on raw detections (VIIRS does not pass) but passes in all three satellites on newly active grid cells: detections after a day without a detection, not verified ignitions.
- Exploratory map: in India the Sunday dip sits almost entirely in the northeast (19 of 26 cells significant after false-discovery correction, 14 of 21 cells mostly inside India; Aqua agrees); the rest of India shows none.
- Within India, the Sunday dip is concentrated in the northeastern hill states, deepest in Nagaland, Mizoram and Manipur, where Sunday detections fall to about 40% of an average day; no weekly dip is established in the rest of India, including the Punjab crop-burning belt. The cause is unresolved.

**Speaker line:** "A weekly association does not identify ignition cause. A failed rest-day test does not classify fire causes either."

## 7. What is ready and what remains

**Title:** A reproducible record with visible limits

Show the [live app](https://firetrace-bhaktapur-2026.pages.dev/), the [public repository](https://github.com/Water-Mal0ne/FIRETRACE) and NASA FIRMS attribution. No worldwide coverage, 2000-2002 reconstruction or operational forecast is claimed; selected-cell errors stay visible. Include the AI disclosure and "NASA does not endorse this project."

**Closing line:** "Follow the evidence before trusting the trend."
