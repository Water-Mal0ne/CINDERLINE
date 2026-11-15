# FIRETRACE — seven-slide judging deck

The seven sections below are the complete deck. Titles plus on-slide text stay within 40 words; each spoken note is 60–90 words. Sources and production directions are not spoken. Real screenshots show the deployed baseline; FRP and outage-sensitivity results are reviewed branch evidence pending team merge/deployment. Do not imply those new results are already live.

## Slide 1 — Nepal: did fire increase?

### On-slide text

Or did the satellite change?

A historical calendar that tests its own conversion.

### Visual

`submission/assets/live-calendar.jpg`: real Nepal calendar screenshot. Preserve the country, record dates and REAL FIRMS DATA label. The screenshot is an application view, not a before/after proof.

### Speaker notes

A sharper satellite can make the fire record change even when burning has not. FIRETRACE builds a historical calendar on a declared reference scale, and tests whether better-looking numbers preserve the season people need to understand. Start here in Nepal. A hotspot is a satellite detection, and one continuing event can produce many detections. We let a viewer inspect the observations behind a week before interpreting a change across years.

### Sources

[S01] `METHODS.md`; [S08] `web/public/data/Nepal.json`; NASA FIRMS measurement context [S13]. Source identifiers are defined in `submission/JUDGE_QA.md`.

## Slide 2 — Different sensors, different detections

### On-slide text

MODIS: 1 km

VIIRS: 375 m

Keep satellite records separate. Sharper detection can reveal smaller hotspots.

### Visual

`reports/review/aqua_vs_converted_viirs_Nepal.png`: observed Aqua and converted VIIRS comparison, retaining the chart's real labels and caveats. The resolution labels describe the products; they do not represent a controlled resolution experiment.

### Speaker notes

NASA FIRMS supplies thermal hotspot observations. MODIS uses a one-kilometre active-fire product; the VIIRS product we use has 375-metre detections and greater sensitivity to small hotspots. Different counts therefore need not mean different burning. Terra MODIS, Aqua MODIS and Suomi-NPP VIIRS stay separate in our analysis. Aqua supplies the declared comparison scale. Resolution is only one difference: overpass timing, cloud, viewing geometry and retrieval limits still affect the observations and the comparison.

### Sources

[S01] `METHODS.md`; [S13] [NASA FIRMS notes](https://firms.modaps.eosdis.nasa.gov/alerts/notes.php) and [VIIRS product description](https://firms.modaps.eosdis.nasa.gov/content/descriptions/FIRMS_VIIRS_Firehotspots.html).

## Slide 3 — Freeze the correction before testing

### On-slide text

Aqua reference scale

B0: raw VIIRS · B1: global ratio · M1: stratified ratios

Train 2013–2017 → select 2018–2019 → test 2020–2024

### Visual

`submission/assets/live-evidence.jpg`: real evidence card, paired with the three-stage timeline above. `reports/selection_lock.json` is the exact source for frozen model choices and year split. Do not label a training-period example as independent validation.

### Speaker notes

The simplest conversion multiplies VIIRS counts by one ratio learned where Aqua and VIIRS overlap. The detailed candidate uses country, day or night, and reported radiative-power strata, with sparse groups pulled toward the simple ratio. We fit on 2013–2017, select by daily error on 2018–2019, then evaluate the locked choice on 2020–2024. Nepal selects the detailed model; the United States selects the simple one. These are reference-equivalent estimates, not recovered counts of distinct fires.

### Sources

[S01] `reports/selection_lock.json`, `reports/harmonization_model.json`, `pipeline/streaming/prepared_runtime.py`, `METHODS.md`.

## Slide 4 — Check held-out years and failures

### On-slide text

Against Aqua, 2020–2024

| Country | Model | Weekly MAE | Bias |
|---|---|---:|---:|
| Nepal | B1 | 43.3 | +83.8% |
| Nepal | M1 | 11.3 | −8.1% |
| Egypt | M1 | 4.3 | +51.7% |

MAE: Aqua-reference-equivalent detections/week.

NOAA-20: separate-platform check; coverage limits remain.

### Visual

Render the Nepal B1/M1 and Egypt selected rows from `reports/review/layer1_table.csv`, with the same units as `reports/review/layer1_table.md`. Keep the comparison label “Aqua reference.” The NOAA-20 caption refers to `reports/review/noaa20/noaa20_conversion_check.csv`, not independent ground truth.

### Speaker notes

On years withheld from model selection, Nepal's weekly mean absolute error against Aqua falls from 43.3 with the simple conversion to 11.3 with the selected model. Egypt still has positive bias of 51.7 percent, so agreement is uneven. A separate NOAA-20 check applies the saved conversion without refitting in four countries and supports transfer between VIIRS platforms. It is not independent fire truth, and its common-date outage sensitivity remains unfinished. Later seasonal experiments reuse these years and are explicitly retrospective.

### Sources

[S02] `reports/review/layer1_table.csv`, `reports/harmonization_eval.csv`; [S09] `reports/review/noaa20/NOAA20.md`, `reports/review/noaa20/noaa20_conversion_check.csv`; [S10] season sensitivity evidence.

## Slide 5 — Test the season as well as totals

### On-slide text

Calendar · evidence · missing weeks · CSV/ICS

India, retrospective: better totals, worse monthly shape.

Both common-date masks preserve that finding.

### Visual

`submission/assets/live-outage.jpg`: real “no observation” calendar/evidence view. The India comparison is explained in the notes; keep its complete numerical table in `submission/evidence/season/whole_year_comparison.csv` and `submission/evidence/season/SEASON_CHECK.md`. Label the analysis retrospective.

### Speaker notes

Choose a country, switch the calendar scale, and open a week to inspect its measurements. Grey outage weeks remain unknown; downloads preserve the distinction. The seasonal check asks a different question from count error. In India's whole-year comparison, the selected conversion improves agreement in totals but worsens monthly shares against Aqua. Both common-date outage masks preserve that direction. Nepal's monthly-shape improvement also remains. These are retrospective sensitivity results, not forecasts, and masked totals include only commonly retained dates.

### Sources

[S08] `reports/review/OUTAGES.md`, `web/src/App.tsx`; [S10] `submission/evidence/season/SEASON_CHECK.md`, `submission/evidence/season/whole_year_comparison.csv`.

## Slide 6 — Weekly patterns, separate raw streams

### On-slide text

US/Australia: clear. Brazil: qualified.

Four country rules fail. Exploratory maps and failed predictions stay visible.

FRP contrast: Aqua and S-NPP pass; Terra fails.

### Visual

`submission/assets/live-rhythm-map.jpg`: real Weekly Rhythm Index exploratory map, clearly labelled exploratory. The reviewed count-versus-FRP chart is `submission/evidence/frp/count_vs_frp_weekdays.png`, labelled “REAL FIRMS DATA, US daytime 2013-2024.” Keep the full chart accessible in the evidence pack; do not crop away Terra's failed criterion.

### Speaker notes

We reproduce a known weekly pattern in each satellite record separately. Independently, FIRETRACE tests whether its historical calendar survives a change of sensor and calibration. US and Australia show Sunday dips. Brazil's newly active grid cells also pass, but are not verified ignitions. India, Nepal, Bangladesh and Egypt fail the country rule; Nepal's simulation has low power. Northeast India's map is exploratory; the Bangladesh hills prediction failed. US daytime count-versus-FRP passes for Aqua and S-NPP, not Terra, with a later Git receipt.

### Sources

[S04] `reports/official/kill_test_gate.json`; [S05] Nepal simulation; [S06] newly active cell and control checks; [S07] northeast India and Bangladesh prediction; [S11] `submission/evidence/frp/FRP_TEST.md`, `summary.csv`, original protocol and verification receipt; [S13] Earl et al. (2015).

## Slide 7 — Evidence, limits, reproduction

### On-slide text

Historical observations. No cause attribution or forecast.

NASA FIRMS data. Public code. Visible limitations. AI assistance disclosed.

github.com/Water-Mal0ne/FIRETRACE

firetrace-bhaktapur-2026.pages.dev

### Visual

`submission/assets/live-calendar.jpg` as a restrained background crop, with the two public links above and readable NASA FIRMS attribution. No NASA logo or endorsement claim. “NASA does not endorse this project” remains explicit in the project page and source material.

### Speaker notes

Our contribution is an inspectable historical record and a test of what its correction preserves. The calendar covers seven countries; it does not establish fire causes, future risk, or universal calibration accuracy. The public repository retains code, manifests, fixed models, failures and independently checked research outputs. NASA FIRMS provides the observations. Codex and Claude Code assisted with implementation, testing and writing; our team must review the claims before submission. Open the live calendar, then follow a result back to its evidence.

### Sources

[S01] `METHODS.md`; [S08] `README.md`, `LIMITATIONS.md`; [S12] `AI_DISCLOSURE.md`; [S10–S11] independently checked branch evidence. [Live application](https://firetrace-bhaktapur-2026.pages.dev/) · [Repository](https://github.com/Water-Mal0ne/FIRETRACE).
