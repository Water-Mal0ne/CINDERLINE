# CINDERLINE — submission desk checklist

Prepared for the team to review and submit on **15 November 2026, Nepal time (UTC+05:45)**. Target submission: **20:00**; supplied final deadline: **23:59**. Confirm any earlier local judging cutoff with the Kathmandu, Nepal local event organizers at 08:00. No project form has been submitted overnight.

The current [NASA Global Organizing Team answer](https://github.com/nasa/spaceapps/discussions/1858) identifies the fields below. The [demo clarification](https://github.com/nasa/spaceapps/discussions/1991) permits a public slide deck of no more than seven slides or a video shorter than 30 seconds. Our seven-slide PDF is the ready demo; a recording remains optional and has not been made. The main submission-guide webpage returned HTTP 502 during preparation, so the team should compare the live form with this checklist before submitting.

## Identity and registration

| Field | Ready entry / final action |
|---|---|
| Project title | **CINDERLINE — a fire calendar that tests its own conversion** |
| Challenge | **Harmonization of MODIS and VIIRS Hot Spots** |
| Challenge URL | https://www.spaceappschallenge.org/2026/challenges/harmonization-of-modis-and-viirs-hot-spots/ |
| Local event | **Kathmandu, Nepal local event** |
| Venue | [VENUE: fill in] |
| Event confirmation | [Add the Kathmandu, Nepal local event listing link] |
| Registered team name | **[PASTE THE EXACT REGISTERED TEAM NAME]** — do not assume the project name is the team name |
| Official team/project page | **[PASTE THE TEAM'S ACTUAL SPACE APPS URL]** |
| Six registered members | **[1 full name] · [2 full name] · [3 full name] · [4 full name] · [5 full name] · [6 full name]** |
| Registration check | Each person appears on this team at the correct local event; confirm one authorized member owns final submission |

The bracketed identity fields require the team, not invented names or a guessed URL.

## High-level project summary — paste this

CINDERLINE turns NASA FIRMS hotspot observations into an inspectable historical calendar on a declared MODIS Aqua reference scale. Users compare raw and converted records, open a week to see its evidence, distinguish missing observations from recorded zero, and download the results. We compare simple and detailed conversions using frozen training, selection and test periods, retain unfavorable results, and test whether better count agreement preserves seasonal shape. A separate Weekly Rhythm Index reproduces known associations in the original satellite streams. This is a historical research prototype, not a forecast or a claim about ignition causes.

## Project details — paste the reviewed document

Use the complete text in [PROJECT_PAGE.md](PROJECT_PAGE.md), under 500 words. It covers the challenge, NASA data, implementation, results, limitations, separate weekly analysis and AI assistance. Its source identifiers resolve through [JUDGE_QA.md](JUDGE_QA.md) and [the evidence ledger](evidence/SOURCE_LEDGER.md).

If the form separates implementation/tools from the description, use:

> Python implements archive cleaning, frozen calibration, evaluation and statistical checks. The interface uses TypeScript, React, Vite, SVG charts and a custom WebGL globe. Cloudflare Pages hosts the static application. GitHub preserves the source and review history. Processed NASA observations supply the measurements; artificial test fixtures are kept separate.

## Public demo and final-project links

| Field | Link / state |
|---|---|
| Final project | https://cinderline-spaceapps.pages.dev/ — planned URL; deploy to the new `cinderline-spaceapps` Pages project and verify it before submitting |
| Source repository | https://github.com/Water-Mal0ne/FIRETRACE — GitHub API confirmed PUBLIC on 15 November Nepal time; repeat a logged-out check |
| Demo PDF, reviewed branch | https://github.com/Water-Mal0ne/FIRETRACE/blob/submission-final/submission/FIRETRACE_slides.pdf — use once the submission PR is pushed and the PDF opens without sign-in |
| Demo PDF after merge | https://github.com/Water-Mal0ne/FIRETRACE/blob/main/submission/FIRETRACE_slides.pdf — **not ready until the submission PR is merged** |
| Editable slide deck | `submission/FIRETRACE_slides.pptx` — supplementary, not a second demo requirement |
| Optional short video | **[PASTE A PUBLIC/UNLISTED VIDEO URL ONLY IF RECORDED]**; rehearse [VIDEO_SCRIPT.md](VIDEO_SCRIPT.md), measure actual duration below 30 seconds, check captions and logged-out access |

Prefer the checked PDF link if time is short. Do not paste a local Windows path, private review link, or a future `main` path that still returns 404. Recheck the exact selected demo URL after merging; use a commit-pinned URL if the team wants an immutable submission snapshot.

## NASA data resources — paste this

NASA's Fire Information for Resource Management System (FIRMS) provides the active-fire and thermal-anomaly observations. CINDERLINE uses archived Terra MODIS and Aqua MODIS Collection 6.1 detections and the Suomi-NPP VIIRS 375 m product. A separate NOAA-20 VIIRS check tests transfer of the saved conversion; it is not independent ground truth. Product identifiers, source archive paths and fingerprints are recorded in the repository manifests. Nominal pixel resolution describes the detection product, not the size or burned area of a fire.

- [FIRMS country archive downloads](https://firms.modaps.eosdis.nasa.gov/country/)
- [FIRMS active-fire data and archive guidance](https://firms.modaps.eosdis.nasa.gov/content/active_fire/)
- [FIRMS MODIS/VIIRS interpretation notes](https://firms.modaps.eosdis.nasa.gov/alerts/notes.php)
- [VIIRS fire/hotspot product description](https://firms.modaps.eosdis.nasa.gov/content/descriptions/FIRMS_VIIRS_Firehotspots.html)

The calendar is historical, 2003–2024. Do not describe it as a current S-NPP feed: the current NASA product page lists the end of S-NPP coverage in November 2026. No new satellite data were downloaded for the overnight package.

## Space Agency Partner and other resources — paste this

No additional partner-agency dataset is required by the core calendar. NOAA-20 observations are obtained through NASA FIRMS as documented above. Natural Earth geographic boundaries, distributed through world-atlas, provide map context; they are not hotspot data or satellite coverage. IANA time-zone definitions support conversion to local civil dates. Earl, Simmonds and Tapper (2015) is prior literature on weekly fire cycles, not a finding first discovered by CINDERLINE.

- [Natural Earth](https://www.naturalearthdata.com/)
- [world-atlas source and licensing](https://github.com/topojson/world-atlas)
- [IANA Time Zone Database](https://www.iana.org/time-zones)
- [Earl et al. (2015), DOI 10.1002/2015GL066383](https://doi.org/10.1002/2015GL066383)
- Open-source implementation dependencies and versions: `requirements.txt`, `web/package.json`, `web/package-lock.json`; reproduction commands: `README.md` and `METHODS.md`.

## Use of artificial intelligence — paste this

Codex and Claude Code assisted with planning, code, analysis implementation, tests, interface work, documentation and submission drafts. Separate agents implemented and independently checked parts of the work. NASA FIRMS supplies the scientific observations; they are not AI-generated. Synthetic test fixtures are explicitly separate. The team must review the outputs and scientific claims before submitting. The project does not claim independent preregistration: its documents disclose the limits of the original gate chronology and the later Git receipt for the locally specified FRP test. No AI-generated imagery, voice or video is included in this submission package. Full disclosure: `AI_DISCLOSURE.md`.

If the team adds generated narration, images or other AI media later, update this field and `AI_DISCLOSURE.md` before submission.

## Final human checks

- [ ] Review all seven slides and the twenty judge answers; confirm new branch evidence is distinguished from what is deployed.
- [ ] Fill the actual registered team name, six members and official project URL above.
- [ ] Check all pasted live, repository and demo links in a signed-out/private browser; no permission request may block judges.
- [ ] Confirm the local judging timetable, the live form's mandatory fields and English/subtitle requirements.
- [ ] Review and personally accept the site's terms and conditions; no agent has accepted them for the team.
- [ ] Save, preview and submit the official project page; save the submitted URL and confirmation. A GitHub PR, deployment or draft form is not submission.

NASA does not endorse this project. The overnight work leaves reviewable artifacts; it does not claim that team review, merging, deployment, recording or final submission has occurred.
