# CINDERLINE — team briefing

Read before judging. Every teammate should demonstrate one week and explain its limits.

**Our opening:** A sharper satellite can make the fire record change even when burning has not. CINDERLINE builds a historical calendar on a declared reference scale, and tests whether better-looking numbers preserve the season people need to understand.

The calendar converts VIIRS detections to Aqua's reference scale. Separately, the Weekly Rhythm Index checks raw satellite streams for a known association. Harmonization did not discover it. Many detections can come from one continuing event.

## Three numbers to remember

- **375 m:** VIIRS detection resolution; MODIS uses a 1 km product. Different sensitivity can produce different counts. [S13]
- **11.3:** Nepal's selected weekly mean absolute error against Aqua on held-out 2020–2024 data; B1 is 43.3. Units: reference-equivalent detections/week, not percent or true-fire error. [S02]
- **2 of 3:** Aqua and S-NPP pass the fixed US daytime count-versus-FRP comparison under both masks; Terra fails. The streams corroborate each other but are not independent experiments. [S11]

## Explain the conversion

Learn an Aqua-count/VIIRS-count ratio from earlier overlap years, then multiply VIIRS counts by it. B1 uses one ratio; M1 uses country, day/night and reported-power groups, pulling sparse groups toward B1. Validation chooses the model, not each week's desired answer. Egypt and local errors remain visible. India's retrospective comparison shows better totals can accompany worse seasonal shape. [S01–S03, S10]

## Explain the random-weekday test

Account for how often each weekday occurs within each year. Under the null, pick a random weekday from each year's seven indices; average those picks. Repeat and ask how often that average is as low as the stated rest-day result. Apply Bonferroni correction across country/stream tests. This assumes exchangeable weekday labels; it does not eliminate cloud or sampling bias. [S04–S05]

## Demonstrate and qualify

Open Nepal, compare scales, inspect a week, then show missing observations and validation. On rhythm, show the US, Brazil's caveat and a failed country rule. New branch evidence may not be live. FRP is sampled power, not energy or emissions. Season comparisons reuse examined years. The FRP local protocol preceded calculation; its Git receipt did not. [S08, S10–S12]

## Five sentences we must never say

1. “NASA approved our conversion.”
2. “We count the true number of fires.”
3. “Harmonization discovered the human week.”
4. “The Sunday dip proves who caused the fires.”
5. “This calendar predicts the next fire.”

Use: “A tested historical prototype with visible limitations.” NASA provides observations; AI assisted the work; our team reviews the claims. Sources: `JUDGE_QA.md`.

**Team names:** [Member 1] · [Member 2] · [Member 3] · [Member 4] · [Member 5] · [Member 6]
