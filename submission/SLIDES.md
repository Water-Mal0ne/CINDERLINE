# FIRETRACE: seven-slide presentation outline

Draft. Check the event's actual slide and video requirements before submitting. Two acts: harmonization, then the human rhythm. Keep unfavorable results visible.

## 1. The question

**Title:** Did fire activity change, or did our camera change?

Show a real regional record with its instrument labels. When VIIRS joined MODIS in 2012 it saw many more small fires, so a naive joined record appears to jump. A hotspot is a detected pixel, not an independent fire.

**Speaker line:** "An apparent increase can mix real change with a change in what the instrument sees."

## 2. Act 1: one comparable history for seven countries

**Title:** A burning activity calendar on one named scale

Select a country in the calendar (Australia, Bangladesh, Brazil, Egypt, India, Nepal, United States; 2003-2024). Flip the raw versus harmonized toggle to show how much of the apparent jump at the switch to VIIRS is the instrument, and what change remains on the Aqua scale. Show typical season, high-activity windows and unusual weeks. This is historical context, not a forecast.

## 3. Act 1: the method and the honest test

**Title:** Separate streams, one reference, a locked evaluation

FIRMS archives, local civil dates, Terra/Aqua/VIIRS kept separate, MODIS-Aqua-equivalent scale. B0 is uncalibrated VIIRS, B1 one training ratio, M1 ratios by country, day/night and fire intensity. Train 2013-2017, select 2018-2019, test once 2020-2024.

| Country | Selected | Selected monthly MAE | Comparator | Remaining limitation |
|---|---|---:|---:|---|
| Nepal | M1 | 30.24 | B1: 182.52 | -8.11% bias |
| United States | B1 | 1,537.79 | M1: 2,078.57 | simpler model wins |
| Egypt | M1 | 15.04 | B1: 90.40 | +51.68% bias |

Units are Aqua-equivalent detections, not fire counts.

## 4. Act 1: one week, back to its evidence

**Title:** Follow the evidence before trusting the trend

Open one week: separate sensor counts, the converted estimate and its bounds, the held-out results, then a share link that reopens the same view.

## 5. Act 2: the human rhythm test

**Title:** Nature has no seven-day cycle; people do

Rest days fixed in advance: Sunday (US, Australia, Brazil, India), Saturday (Nepal), Friday (Bangladesh, Egypt). Pass rule fixed in advance: the US replicates the known Sunday dip, and at least two other countries show their rest day as the lowest weekday, significant after correction, in at least two of three satellite streams.

**Result: pass.** US 3/3 streams (Sunday 22-33% below an average day), Australia 3/3, Brazil 2/3. India, Nepal, Bangladesh and Egypt fail. Show the Human rhythm tab: weekday bars with 95% intervals, rest day highlighted.

## 6. Act 2: what it does and does not show

**Title:** The caveats are part of the result

- All three passing countries rest on Sunday; Friday- and Saturday-rest countries did not show a dip, so this does not show the dip following each country's own rest day.
- Brazil's Terra static-source control also dips on Sunday (index 0.913, adjusted p = 0.021), so Brazil's vegetation-fire dip cannot be cleanly separated from weekly patterns in industrial heat sources. Its support is weaker than the US and Australia, whose static controls are clean.
- Exploratory map: in India the Sunday dip sits almost entirely in the northeast (19 of 26 cells significant after false-discovery correction, Aqua agrees); the rest of India shows none.
- Within India, the Sunday dip is concentrated in the northeast. It is deepest in Nagaland, Mizoram and Manipur, where Sunday detections fall to about 40% of an average day, and it is just as deep in the Indian cells along the border with Myanmar. Nagaland and Mizoram are mostly Christian and Manipur is about 41% Christian, and in many of these communities Sunday is widely kept as a church day. The link is not clean: Meghalaya, also mostly Christian, shows a weaker dip, and Assam, mostly not Christian, still shows one. This is an exploratory correlation, not evidence of what causes the pattern. (Religion shares: Census of India 2011.)

**Speaker line:** "A dip is consistent with people scheduling their burning. It is not proof of who lit the fires."

## 7. What is ready and what remains

**Title:** A reproducible record with visible limits

Show the [live app](https://firetrace-bhaktapur-2026.pages.dev/), the [public repository](https://github.com/Water-Mal0ne/FIRETRACE) and NASA FIRMS attribution. No worldwide coverage, 2000-2002 reconstruction or operational forecast is claimed; selected-cell errors stay visible. Include the AI disclosure and "NASA does not endorse this project."

**Closing line:** "Follow the evidence before trusting the trend."
