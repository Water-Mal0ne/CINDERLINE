# FIRETRACE hackathon readiness and creative review

Reviewed November 14, 2026 against `FIRETRACE_codex_prompt (2).md`, the implemented application, scientific reports and submission drafts. This review is independent of the data implementation. At review time, the two-country release is public and the seven-country release is being integrated. Passing a code test is not proof of a flawless demonstration or an award outcome.

## Recommended signature

**“Did the landscape change, or did the instrument change? Follow the same observation through the evidence.”**

The strongest working contribution is the connected path from geography to comparison to evidence: orient on the Earth, inspect one actual period, see separate Aqua and VIIRS observations alongside the converted estimate, check held-out evaluation, then share that exact selection. Each step answers a user question. The globe gives location; the comparison explains the challenge; the evidence makes the result inspectable. Lead with that path rather than the number of features or countries.

The original second act, a general human-rhythm discovery, is **not a supported product claim**. The seven-country candidate's statistical criterion passes for the US, Australia and Brazil, but Brazil's matched controls are flagged. The overall decision remains `insufficient_data`, with `production_allowed: false`. Only Australia qualifies beyond the US, short of the required two other countries. Keep the optional module closed, explain this finding in the report, and do not reinterpret an inconclusive gate as proof that no rhythm exists.

## Scope against the brief

| Objective | Assessment and acceptance condition |
| --- | --- |
| Harmonized record with separate streams and named Aqua reference | Implemented. The new global training ratio changes when the training population expands to seven countries; publish the corresponding model revision, evaluation and source manifest together. Do not reuse the old two-country numbers in the pitch. |
| Fixed training, validation and held-out evaluation | The independent phase-3 audit verifies training-only selection, fixed model choices and exact count reconciliation. Preserve the selection lock and all baseline results. Do not tune from the expanded held-out table. |
| Historical burning calendar, seasonal profile, unusual weeks and critical windows | Implemented for supported national series and selected daily cells. Historical windows are not forecasts; national seasonality remains national when a cell is selected. Verify that those scope labels survive mobile layout and evidence sharing. |
| All seven preset countries | Seven-country candidate is ready for integration, not yet evidence of public behavior. Acceptance requires one browser workflow in each country and a published-asset verification after deployment. |
| Any grid cell inside a region | Partial. Annual inspection covers all 41,986 contributing cells in the candidate; daily calendars cover 12 training-selected cells per country. This is a deliberate product limit, not arbitrary-area daily coverage. Keep it visible in the app and submission. |
| 2000–present history / early Terra bridge | Partial. Supported local years are 2003–2024. No early Terra bridge is validated. Do not describe it as rejected after a failed validation if it was not implemented and tested. |
| 0.5-degree grid sensitivity | Not completed in the reviewed reports. The brief requests it. Record it as a remaining scientific check; do not equate the 0.25-degree unit tests with this sensitivity study. National linear-ratio totals may be invariant to grid aggregation by construction, which would not establish cell-level robustness. |
| Synthetic sensor-switch check | Figure and numerical outputs are present. Keep the synthetic label inside the visual; use it to explain the mechanism, separately from real-data performance. |
| Rhythm analysis, diagnostics and gate | Implemented and correctly withheld. A negative or inconclusive scientific result does not justify changing the prespecified threshold to obtain a more dramatic demo. |
| Reproduction and payload budget | Canonical streaming source and CLI are being packaged. The lossless candidate projects 49.57 MiB, with only about 455 kB of headroom under 50 MiB. Verify the actual final build, not only the data estimate. All daily rows must round-trip exactly. |
| CSV/ICS downloads, public site and share links | Implemented. Verify the download contents for a selected cell and a partial year, valid calendar line endings, and fresh-navigation restoration after publication. Share links use current published data, not an immutable scientific snapshot. |
| Submission materials and judge access | Drafts exist; a recorded video or finished slide deck is not established by a script/outline. Update the final scope and metrics, verify the allowed format, check every submission link without sign-in, and confirm the team actually submits before the deadline. The repository remains private by the user's explicit choice. |

## Fixes accepted during this review

1. **Make spatial scope visible inside every evidence card.** The reviewed heading named only the country and week even when the data were for one cell. A screenshot could be read as a national total. The coordinator accepted a visible whole-region/cell identifier and location in the drawer. Acceptance: open the same week nationally and for a selected cell, and distinguish them without looking behind the modal; a reopened share link retains that context.
2. **Clarify the raw/harmonized control's scope.** It sits above the globe, while Earth always uses the common Aqua reference scale. The coordinator accepted an explicit note. Acceptance: a person can identify which visual changes with the toggle and which stays on the reference scale. Do not add raw annual Earth layers solely to solve this wording problem; they would consume budget and introduce more comparability work.
3. **Refresh the narrative as one release.** The original drafts say only two countries were evaluated. The seven-country gate has a different reason for remaining closed, and global-ratio values change with the training population. A documentation agent owns the synchronized update. Acceptance: README, methods, limitations, model table, project page, slides and video script all describe the deployed model revision.

The first two fixes were accepted and in progress when this report was written; this report does not substitute for the coordinator's final browser verification.

## Two bounded creative improvements

### 1. Treat the existing evidence journey as the demonstration

Use the three observed/converted numbers already implemented for one real shared week. Say what each number measures, open the evidence card, then show the complete held-out table. The illustrative week must keep its selection explanation; it is not an accuracy benchmark. End by copying its share link so a judge can retrace the interaction.

This needs rehearsal and clearer emphasis, not a new model. It makes the creative experience serve the challenge's scientific question. A brief Earth orientation is enough; do not spend most of a 30-second demonstration orbiting a globe before reaching the actual comparison.

### 2. Give an evidence export a release identity

A later small enhancement can put the country/cell, exact dates, model, reference scale and a stable data/model revision identifier together in the evidence export and Methods view. Use a fingerprint that includes analysis configuration/model as well as source archives. A source-manifest hash alone cannot distinguish a changed model fitted to the same archives.

Acceptance: the identifier matches a saved release record and exported values; reopening an old link against newer data explicitly says it uses the current release. Do not call a mutable share URL an immutable snapshot. This enhancement is optional after the current release gates pass and should not displace final QA or the actual submission.

## Final demonstration acceptance sequence

1. Open the public site from a clean session. Choose Nepal, then another climate/hemisphere such as Australia or Brazil. Record the browser, viewport and network conditions instead of making an unmeasured “under three seconds” claim.
2. Orient the Earth, focus the country, change the year, inspect an annual cell, and return from the accessible grid table. Unprocessed geography stays distinct from zero recorded detections.
3. Open a supported daily cell. Confirm the cell identity and dates, switch the calendar scale, inspect a week, and reconcile its displayed totals with the downloaded evidence.
4. Show one historical high/low period and explain the national comparison, partial-week rule and unmeasured observation coverage.
5. Show the selected model alongside every baseline in the held-out table, including a country where the simpler ratio wins. Do not present selected examples as the entire evaluation.
6. Share and reopen the view on mobile. Confirm country, daily cell, range, scale and evidence week. Test invalid-link recovery and keyboard focus, including closing share details without closing the evidence dialog.
7. Finish on the correct live URL, NASA-data attribution, AI disclosure and accessible submission assets. Keep the rhythm feature absent unless the unchanged gate actually passes.

## Official event context checked

The official 2026 overview lists November 14–15 and a project deadline of November 15 at 11:59 p.m. local time. It also describes registration and team/project submission as steps for global-judging eligibility; this review did not inspect the team's account or submission status. [NASA Space Apps 2026](https://www.spaceappschallenge.org/2026/)

A Navigator answer in NASA's official discussion repository confirms that a selected country or region is acceptable and emphasizes harmonization and a meaningful calendar over attempting worldwide coverage. This supports a clearly scoped regional prototype; it does not remove the team's duty to state its daily-cell and temporal limits. [Challenge scope guidance](https://github.com/nasa/spaceapps/discussions/2016)

The official discussion guidance describes a short public demo, English content or subtitles and AI-tool disclosure. The current submission-guide and challenge-detail pages returned HTTP 502 in this review, so their full current wording was not independently retrieved. The team must verify the actual form and local-event instructions before final submission. This review does **not** establish a mandatory public-GitHub-repository rule and does not authorize changing the user's private repository visibility. [Submission discussion](https://github.com/nasa/spaceapps/discussions/1973), [official submission guide](https://www.spaceappschallenge.org/resources/project-submission-guide/), [official challenge](https://www.spaceappschallenge.org/2026/challenges/harmonization-of-modis-and-viirs-hot-spots/)

The closest strategic fit is rigorous use of science/data with a clear local-use story. Award selection is a judgment by the event; a large feature count, a successful build or a striking globe does not guarantee a win.
