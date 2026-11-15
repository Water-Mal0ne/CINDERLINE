# CINDERLINE

**Challenge:** Harmonization of MODIS and VIIRS Hot Spots

**Team:** Kathmandu, Nepal local event

*Two satellites. One unbroken fire record.*

A sharper satellite can make the fire record change even when burning has not. CINDERLINE builds a historical calendar on a declared reference scale, and tests whether better-looking numbers preserve the season people need to understand.

NASA FIRMS observations come from instruments with different detection characteristics. We compare uncalibrated VIIRS, one global conversion ratio, and stratified ratios against MODIS Aqua. Training uses 2013–2017, model selection 2018–2019, and locked evaluation 2020–2024. Nepal's weekly mean absolute error falls from 43.3 with the simple ratio to 11.3 with its selected model. Egypt retains +51.7% weekly bias. These measure agreement with Aqua, not true fire counts. An out-of-sample 2025 check is weaker: converted VIIRS keeps the weekly timing, but its totals run 21% below Aqua in Brazil and 18% in Nepal, so 2025 is labelled beyond the validation period. [S01–S02]

The calendar covers Australia, Bangladesh, Brazil, Egypt, India, Nepal and the United States, 2003–2024, plus 2025 as converted VIIRS. Users compare raw and harmonized views, inspect weekly evidence, compare each month with the same month in other years, draw or type their own area (national calibration; local accuracy not validated), distinguish outage weeks from recorded zero, explore annual geography, and export CSV or historical ICS references. It supports historical exploration, not forecasts or emergency alerts. [S08]

We also test whether conversion preserves seasonal shape. In India's retrospective whole-year comparison, a better annual total accompanies worse monthly-share agreement. That direction survives both common-date outage masks; Nepal's seasonal improvement also survives. The full results retain simple baselines and failures. [S10]

We reproduce a known weekly pattern in each satellite record separately. Independently, CINDERLINE tests whether its historical calendar survives a change of sensor and calibration.

The official country rule passes for the US, Australia and Brazil; India, Nepal, Bangladesh and Egypt do not pass. All passing countries test Sunday. Brazil's evidence is weaker under stricter controls. Newly active grid cells are not verified ignitions. Northeast India's map is exploratory, Nepal's simulation shows limited power, and a Bangladesh hills prediction failed. No result identifies who burns or why. [S04–S07, S13]

A separate fixed US daytime comparison finds a smaller Sunday deficit in sampled radiative power than in counts for Aqua and S-NPP; Terra fails the criterion. The same observations, both outage masks and independent recomputation are retained. Its protocol was locally frozen before analysis, but the Git receipt came after the original result. Summed FRP is not energy, emissions or burned area. [S11]

[Live application](https://cinderline-spaceapps.pages.dev/) · [Source repository](https://github.com/Water-Mal0ne/FIRETRACE) · [NASA FIRMS](https://firms.modaps.eosdis.nasa.gov/country/)

**AI disclosure:** Codex and Claude Code assisted with implementation, testing and writing; the team must review the scientific claims before submission. See `AI_DISCLOSURE.md`. NASA does not endorse this project. [S12]

Sources [S01–S13]: `submission/JUDGE_QA.md` and the submission evidence ledger. The live site shows these additions only after redeployment.
