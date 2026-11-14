# FIRETRACE morning handoff — 15 November 2026, Nepal

Prepared after the bounded overnight cycle. **Nothing was merged or deployed.**
The existing live site remains the safe baseline. This report is a handoff, not a
claim that work continues unattended after the cycle ends.

## Ten-line summary

1. Five reviewable PRs are ready: story #5, FRP #6, UI #7, season #8 and submission #9.
2. Main remains `290e756`; the original UI backup and Workers migration worktree are untouched.
3. The story now separates the harmonized historical calendar from rhythm measured in raw streams.
4. The fixed US daytime count/FRP comparison passes for Aqua and S-NPP; Terra fails its interval criterion.
5. Its local protocol preceded calculation, but its Git receipt followed the known result: no prior Git preregistration claim.
6. India's better totals/worse seasonal shape and Nepal's seasonal improvement survive both common-date masks.
7. UI work makes the scale switch prominent, improves phone reading and preserves calendar-first/lazy-globe behavior.
8. Seven slides, PDF/PPTX, scripts, a project page, twenty judge answers and a team briefing are ready.
9. The combined candidate passed 81 Python tests, 45 web tests, three web prechecks, build and browser checks.
10. Review two documentation merge resolutions, merge deliberately, retest, deploy and submit before the local cutoff.

## Tasks and PRs

| Task | Status | Review link | Result and qualification |
|---|---|---|---|
| 1 — Story wording | Done | [#5](https://github.com/Water-Mal0ne/FIRETRACE/pull/5) | Known weekly pattern analyzed separately in each raw stream; no cause or discovery claim. NOAA-20 is transfer corroboration, not independent fire truth. |
| 2 — Count versus FRP | Partial against the literal chronology requirement; analysis, independent check and panel done | [#6](https://github.com/Water-Mal0ne/FIRETRACE/pull/6) | Fixed gate passes in the same two streams under both masks. The required Git-before-result sequence cannot truthfully be supplied because the result already existed. See chronology below. |
| 3 — UI polish | Done | [#7](https://github.com/Water-Mal0ne/FIRETRACE/pull/7) | Visible scale control, phone navigation/readability, keyboard-scroll tables and paginated regional fallback. Scientific text and values remain owned by the separate story/data changes. |
| 4 — Season sensitivity | Done | [#8](https://github.com/Water-Mal0ne/FIRETRACE/pull/8) | Existing experiment repeated under common 73-date and padded 87-date masks; India/Nepal directions survive. Retrospective sensitivity, not a fresh holdout. |
| 5 — Submission package | Done; human identity/submission actions remain | [#9](https://github.com/Water-Mal0ne/FIRETRACE/pull/9) | Seven slides, 419-word project page, twenty answers, 432-word briefing, short/live scripts and field checklist. Real evidence, 38 hash-pinned source snapshots. |
| 6 — Cross-PR audit | Done | [audit](reports/review/overnight/INTEGRATION_AUDIT.md) | No unresolved numerical contradiction or application-code conflict. Two deliberate document resolutions described below. Final actual merge must be retested. |
| 7 — Morning report | Prepared here; final commit/push/check receipt accompanies delivery | [#9](https://github.com/Water-Mal0ne/FIRETRACE/pull/9) | This file, preserved audit receipts and an outside-worktree copy; no further feature work. |

### Exact source heads audited

| Branch | Head | Python / web tests at that head |
|---|---|---|
| `story-wording` | `ff4a64e8a78fdf6a1bb37dc3f0cb37a0bceaab2b` | 70 / 30 |
| `frp-test` | `cf2f4d364fa8dc3fdd2e51108b4a76466f7f51c1` | 75 / 35 |
| `ui-polish-v2` | `cb54eaca2f5a857cfe541dcb0509495413c2f120` | 69 / 40 |
| `season-check` | `9ee15afe972cca97322ea371b1fdf3a66b45a0b6` | 74 / 30 |
| `submission-final` package before this handoff | `e2568365ac6e0c7166ba305c2546177bded8917c` | 70 / 30 |

Each also passed the three web prechecks and production build. This report and
audit files are a documentation-only follow-up to the last row; use
`git log -1 --format=fuller -- MORNING_REPORT.md` for their delivery commit.
The final post-commit receipt is saved outside the repository with the report,
avoiding a self-referential commit hash inside its own file.

## Scientific results to explain honestly

The main product is a historical 2003–2024 calendar on Aqua's reference scale for
seven countries. Training is 2013–2017, model selection 2018–2019 and held-out
evaluation 2020–2024. Nepal's weekly MAE against Aqua improves from B1 **43.3** to
selected M1 **11.3**, while bias changes from **+83.8%** to **−8.1%**. Egypt still
has **+51.7%** bias with M1, despite weekly MAE **4.3**. These measure agreement
with a reference sensor, not error against the true number of fires.
Sources: the frozen Layer 1 evaluation and `submission/evidence/CLAIM_AUDIT.md`.

### FRP verdict and chronology

**PASS under the fixed numerical rule in Aqua and S-NPP; Terra FAILS.**

> In US daytime observations from 2013-2024, the Sunday deficit was stronger in detection counts than in summed fire radiative power in MODIS Aqua and VIIRS S-NPP, under a pre-specified test.

“Pre-specified” here refers to the preserved local protocol. It does not mean an
external preregistration or a prediction committed to Git before the result.

- Git protocol receipt: **`92626ed2f76fc6ab1bcefa6254d49609b7c6b982`**. Its protocol/prediction block is preserved unchanged. **This Git commit was made after the outcome was already known.**
- Original local protocol freeze: **2026-11-14 18:57:23.284 UTC**, SHA-256 **`1B88C8B3C7A1225FB2AA10E3B19DD9311CB7F4B022A9795C51552557BB434171`**.
- Original runner calculation: approximately **19:00:58–19:01 UTC**; first cross-implementation agreement receipt approximately **19:02:51 UTC**. The independent results were generated at approximately **19:00:33 UTC**. These are local provenance records, not external timestamp certification.
- The new portable independent receipt reproduces the result and pins current scripts/artifacts. It does not turn a retrospective Git receipt into a prospective one.

US vegetation detections, daytime, 2013–2024; streams separate, IANA local dates,
matched finite nonnegative FRP detections for counts and power, equal-weight
twelve-year blocks, 50,000 paired year bootstrap draws, adjusted 98.333% intervals.
Official unmasked daytime counts reconcile exactly: Terra **460,657**, Aqua
**631,342**, S-NPP **2,784,451**. The common-date analytical cohort is intentionally
smaller. Missing FRP is never replaced with zero.

| Stream | Primary Sunday count index | Primary Sunday summed-FRP index | Difference | Adjusted interval | Primary / padded gate |
|---|---:|---:|---:|---|---|
| Terra | 0.6280 | 0.7217 | 0.0937 | −0.0017 to 0.2046 | Fail / fail |
| Aqua | 0.6443 | 0.8145 | 0.1703 | 0.1019 to 0.2438 | Pass / pass |
| S-NPP | 0.6545 | 0.7455 | 0.0909 | 0.0451 to 0.1370 | Pass / pass |

Both passing streams retain positive leave-one-year-out and highest-FRP-day
removal results under both masks. This is supporting evidence, not a replacement
for the calendar or proof of mechanism. Summed FRP is sampled radiative power,
**not energy, emissions, burned area, fire counts, fire size or severity**.
Sources after merge: `reports/review/frp/FRP_TEST.md`, `pipeline/review/frp_test.py`
and `scripts/verify_frp_test.py`; pinned copies already accompany PR #9.

### Season preservation

| Country / dates retained | Absolute total error, B1 → M1 (%) | Monthly shape distance, B1 → M1 (TV ×100) |
|---|---:|---:|
| India, original unmasked | 16.46 → 3.80 | 13.59 → 16.29 |
| India, common mask | 13.83 → 4.05 | 12.31 → 15.57 |
| India, padded mask | 13.94 → 4.51 | 12.28 → 15.42 |
| Nepal, original unmasked | 83.34 → 7.91 | 14.55 → 4.51 |
| Nepal, common mask | 77.67 → 8.30 | 13.82 → 5.75 |
| Nepal, padded mask | 76.74 → 8.06 | 13.79 → 5.69 |

Lower is better. India's improved total agreement does **not** imply preserved
monthly shape. Nepal's seasonal improvement keeps its direction. These are
descriptive means, not claims that every year/cut wins. Masked totals cover common
retained dates; they do not reconstruct missing full-year activity. Frozen models
and original results remain unchanged. All 4,095 scenarios and 12,789 daily rows
were independently reproduced. Source after merge:
`reports/review/season/SEASON_CHECK.md`; pinned evidence already accompanies PR #9.

### Limits that must remain visible

- The weekly association was already known. It is measured separately in raw streams and does not identify who burns, why, religion or human causation.
- Brazil's newly active cells are not verified ignitions; its long-record industrial control weakens the interpretation.
- Nepal's low country-level simulated power cannot establish absence of an effect. Bangladesh's geographic prediction failed; the northeast India map remains exploratory.
- NOAA-20 is a separate-platform transfer check; strict common-date coverage sensitivity for that check remains unfinished. Shared disagreement does not diagnose a cause.
- Daily calibration bounds are not a weekly confidence interval. Held-out sensor agreement is not ground-truth validation or NASA approval.
- Outage weeks can contain both a recorded zero day and unavailable days; the whole unavailable week must not become zero.
- No forecasting, risk scoring, warnings, first-discovery claim or operational-safety claim is supported.

## Merge plan and known collisions

**Recommended order: #5 → #6 → #7 → #8 → #9.** All five passed their branch
checks; their combined application passed the integration rehearsal. They are
ready for human review, not authorized for automatic merging.

1. **#5 story:** preserve corrected scientific wording and chronology.
2. **#6 FRP:** retain its fixed US-only panel, Terra failure, local/Git timing caveat and immutable protocol.
3. **#7 UI:** retain both sets of test suites, phone styles and accessibility changes.
4. **#8 season:** resolve `submission/JUDGE_QA.md` by keeping corrected story questions 1–17 and the exact season question 18. Story already contains this verified Q18. Do not restore the older answers wholesale.
5. **#9 submission:** the complete final twenty-answer Q&A deliberately supersedes that intermediate draft. Resolve the chained `DECISIONS.md` conflict by retaining all base and five-task sections, including the new handoff section. The prepared [resolution](reports/review/overnight/DECISIONS.resolved.md) preserves the full union; inspect it against the actual current files before use.

The final pairwise conflict inventory contains only Q&A conflicts, but the actual
five-step rehearsal also produces a **DECISIONS conflict at the last step**.
There were no application-code/scientific-code conflicts. Do not use a wholesale
“ours” or “theirs” resolution for these documents.

The tested combined source tree is
`d908acdbca8d5bf20a033f7cac77946636be59b3`. It was an exported simulation, not a real
branch merge. All 524 tracked files remained unchanged after checking; 15 official
result files and four sample files match main. Existing public numerical data and
frozen models match main; only approved explanatory strings change in the old
rhythm payload, with FRP added separately.

If time is short, **#7 is the first optional merge**: the baseline UI remains
usable. #6's app panel and #8's additional source analysis can also be deferred,
but PR #9's slides already discuss their verified, pinned evidence; explicitly
distinguish report evidence from what is live and omit those demo clicks. That
reduced merge combination has not been tested here and needs its own checks. Do
not skip #5's claim corrections. Keep main/live unchanged if any resulting merge
cannot be validated before the cutoff; do not rush an untested production update.

## Validation and remaining product limitations

Combined checks: **81 Python tests; 45 web tests plus three prechecks; build PASS**.
Distribution: **126 files, 52,271,113 bytes (49.85 MiB)**, `index.html` present;
largest file `globe.json` **12,999,487 bytes (12.40 MiB)**; no file above 25 MiB.
These sizes describe the exact archive-exported candidate; checkout line endings
can change totals slightly. Measure the actual final build again.

The first combined build hit an esbuild sandbox ancestor-directory read denial.
A permission-only retry passed; no source/dependency change. An earlier archive
export's CRLF conversion was detected by the exact-byte guard and corrected by
exporting with conversion disabled, without changing repository configuration.
Both failed attempts remain recorded rather than hidden. Vite still emits its
existing large lazy-globe chunk warning.

Actual combined browser checks passed:

- Calendar-first loading; seven country selectors, each with 1,166 weekly buttons, no alert or empty calendar; raw/harmonized scale and one Nepal daily grid cell.
- Nepal 2024 week 28: July 8 recorded zero, July 9–14 unavailable, whole-week estimate unavailable; evidence dialog and Escape close work.
- `?view=rhythm` restores the tab. US FRP shows the fixed result and failed Terra interval; selecting Nepal removes that US-only panel.
- A 390-pixel phone viewport has no page-wide horizontal overflow; the FRP evidence table scrolls by keyboard and the caveats remain visible.
- The on-demand 3D globe renders with no browser console errors; its grid table shows pagination. Earlier UI checks covered all 84 daily cells; the combined browser run repeated seven national calendars and one cell, not all 84 again.
- Desktop controls are visible and the combined screenshots are saved with the outside-worktree handoff.

Existing limits deliberately retained: the Rhythm country picker is independent
of calendar region and is not restored by the URL; switching/remounting can reset
it to the US. Annual globe camera/view state is not share-link state. These are
not claims of broken data, but the demo must not promise those restoration features.

## Submission materials and human actions

Start with [TEAM_BRIEFING](submission/TEAM_BRIEFING.md), then
[JUDGE_QA](submission/JUDGE_QA.md) and
[SUBMISSION_CHECKLIST](submission/SUBMISSION_CHECKLIST.md).

- [Seven-slide PDF](submission/FIRETRACE_slides.pdf) and [editable PPTX](submission/FIRETRACE_slides.pptx); authored title/body counts 17–35 words, notes 70–82 words. Real chart labels are retained separately.
- [Slide source](submission/SLIDES.md), [short/live scripts](submission/VIDEO_SCRIPT.md), [419-word project page](submission/PROJECT_PAGE.md).
- PDF SHA-256: `2db65365ff2de1eea4615f7fab2fc73069919560a644d3da239a6c4f8d7371d0`; PPTX SHA-256: `55cfdf62a1e1904df94772af8af52ee1aa635e7b797322a964c32442df313a1e`.
- The PDF is raster, generated from the reviewed slide renders because native PDF export lacked a font dependency. It is not tagged accessible text. Markdown provides selectable text and the PPTX preserves editable titles/body/table/notes; desktop PowerPoint save/reopen was not tested.
- The short script is 70 spoken words, targeting under 30 seconds; **time an actual recording**. The separate 271-word live pitch is not the short demo. A seven-slide PDF is ready if the team does not record a video.
- Fill the registered team name, all six members and actual official team/project URL. Confirm the Bhaktapur/Khwopa local judging deadline with the organizers. The supplied Sunday 23:59 cutoff is not a substitute for an earlier local cutoff.
- The repository is public. Anonymous requests to the repo, branch PDF/PPTX and current live site returned HTTP 200; the downloaded artifacts matched their hashes. Repeat these checks after merging and before submission. No account login, terms acceptance or actual submission was performed.

## Exact morning release commands — only after approved merges

Run this entire PowerShell block as one script from the main FIRETRACE worktree,
so a thrown error stops the sequence. This is a future checklist;
**none of these deployment commands were run overnight**. Use the existing Python
environment. Stop on every failure. `github`, not `origin`, is the remote.

```powershell
$ErrorActionPreference = 'Stop'
function Invoke-Checked {
    param([string]$Program, [string[]]$Arguments)
    & $Program @Arguments
    if ($LASTEXITCODE -ne 0) { throw "$Program failed with exit code $LASTEXITCODE" }
}

if (@(git status --porcelain).Count -ne 0) {
    git status --short
    throw 'Working tree has changes; preserve them and stop.'
}
Invoke-Checked 'git' @('fetch', 'github')
$taskBranch = (git branch --show-current).Trim()
$taskUnpublished = @(git log --oneline 'HEAD' '--not' '--remotes=github')
if ($taskUnpublished.Count -gt 0) {
    $taskUnpublished
    throw 'Current branch has unpublished commits; preserve them and stop.'
}
if ($taskBranch -ne 'main') { Invoke-Checked 'git' @('checkout', 'main') }
Invoke-Checked 'git' @('rev-parse', '--verify', 'github/main')
$taskAhead = [int](git rev-list --count 'github/main..main')
if ($taskAhead -gt 0) {
    git log --oneline 'github/main..main'
    throw 'Local main has commits not on github/main; preserve them and stop.'
}
Invoke-Checked 'git' @('pull', '--ff-only', 'github', 'main')
Invoke-Checked 'git' @('merge-base', '--is-ancestor', '290e756', 'HEAD')
Invoke-Checked 'git' @('log', '-1', '--format=fuller')
$taskReleaseCommit = (git rev-parse HEAD).Trim()

Invoke-Checked 'npm.cmd' @('ci', '--prefix', 'web')
$taskRun = Join-Path (Get-Location) ('work/release-' + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $taskRun | Out-Null
$taskPython = (Resolve-Path -LiteralPath '.venv/Scripts/python.exe').Path
Invoke-Checked $taskPython @('-m', 'pytest', 'tests', '-q', '--basetemp', (Join-Path $taskRun 'temp'), '-o', ('cache_dir=' + (Join-Path $taskRun 'cache')))
Invoke-Checked 'npm.cmd' @('--prefix', 'web', 'test')
Invoke-Checked $taskPython @('scripts/build_submission_facts.py', '--check', '--audit-docs')
Invoke-Checked 'npm.cmd' @('run', 'build')
if (-not (Test-Path -LiteralPath 'dist/index.html')) { throw 'Missing dist/index.html' }
$taskAssets = @(Get-ChildItem -LiteralPath 'dist' -File -Recurse)
$taskBytes = ($taskAssets | Measure-Object -Property Length -Sum).Sum
Write-Output ("Built {0} files, {1} bytes, {2:N2} MiB" -f $taskAssets.Count, $taskBytes, ($taskBytes / 1MB))
$taskLarge = @($taskAssets | Where-Object Length -gt 25MB)
if ($taskLarge.Count -gt 0) { $taskLarge; throw 'Asset exceeds Pages 25 MiB limit' }
if (@(git status --porcelain).Count -ne 0) {
    git status --short
    throw 'Checks changed tracked/unignored files; inspect before deploying.'
}
if ((git rev-parse HEAD).Trim() -ne $taskReleaseCommit) {
    throw 'HEAD changed during release checks; stop and rebuild.'
}
Invoke-Checked 'npx.cmd' @('--yes', 'wrangler@4.162.0', 'pages', 'deploy', 'dist', '--project-name', 'firetrace-bhaktapur-2026', '--branch', 'main')
Invoke-Checked $taskPython @('scripts/verify_deployment.py', '--url', 'https://firetrace-bhaktapur-2026.pages.dev/', '--dist', 'dist', '--report', (Join-Path $taskRun 'deployment_verification.json'))
Write-Output ("Verified deployed commit: " + $taskReleaseCommit)
```

If Wrangler reports no login, stop this sequence. The account owner may run the
following **in the morning**, approve it in their browser, then repeat the deploy
and verification lines. Never put credentials in chat or the repo.

```powershell
npx --yes wrangler@4.162.0 login --scopes account:read user:read pages:write
```

Record the exact deployment URL Wrangler prints and the deployed commit. Do not
use the Workers project or migrate hosting as part of this release.

### Six live checks after deployment

1. **Asset identity:** `verify_deployment.py` passes for every generated asset against the production Pages URL, with its receipt outside tracked reports.
2. **Calendar:** all seven countries load; raw/harmonized toggle changes and restores state; select a daily grid cell and inspect its calendar without an empty or stale-country state.
3. **Evidence:** a normal week opens; Nepal 2024 week 28 distinguishes a recorded zero from unavailable days and keeps the weekly estimate unavailable; no invented weekly confidence interval.
4. **Rhythm:** the tab exists, `?view=rhythm` opens it, country controls work, caveats are visible; if #6 is merged, FRP appears only for the US and Terra's failed criterion remains visible.
5. **Earth:** calendar opens before the globe; explicit Open 3D Earth loads it, interactions work and the accessible paginated table remains usable.
6. **Phone and sharing:** at 390 px, read charts/tables/caveats, use keyboard/focus controls, download CSV/ICS, reopen a share link within its documented scope, and open the repo/demo artifacts logged out.

## Team schedule — Nepal time, Sunday 15 November

| Time | Work and owner |
|---|---|
| 08:00–08:30 | All six read the briefing. Assign release owner, science reviewer, UI reviewer, presenter, submission owner and independent checker. Confirm actual registered team identity and any earlier local judging cutoff. |
| 08:30–09:30 | Review and merge #5 → #6 → #7 → #8 → #9 with the documented QA/decision resolutions. Release owner performs merges; a second person checks the resulting documents and hashes. |
| 09:30–10:30 | Run full tests/build, deploy the approved main to existing Pages, record commit/URL and complete all six live checks. Stop if any check fails. |
| 10:30–12:00 | Rehearse the calendar-first demonstration and judge questions. Time the short video if recording; otherwise use the seven-slide PDF. Verify every public link while logged out. |
| 12:00–13:00 | Independent reviewer compares the actual submission fields, deck and live app. Fix only concrete errors within the agreed scope. |
| 13:00–14:00 | Final regression and human scientific sign-off. Freeze links/artifacts and keep a safe fallback. |
| **14:00** | **Feature freeze.** No new analysis, country, feature or claim. Only essential submission/access corrections with review. |
| 14:00–18:00 | Fill the official project fields, six names, NASA/other sources, AI disclosure and final URLs. Submission owner checks local requirements; another teammate reviews everything. |
| 18:00–20:00 | Final logged-out access and required-field check; submit and save the confirmation. **Target submitted by 20:00.** |
| 20:00–23:59 | Buffer for confirmed submission/access problems only, subject to any earlier local deadline. Verify the submission actually appears complete. |

## Audit files and every overnight judgment

The following appendix reproduces the dated overnight sections from the prepared
DECISIONS union, including the immutable FRP protocol and its chronology caveat.
Older project-history decisions remain in the full prepared resolution; they were
not rewritten tonight. Independent audit documents are preserved under
`reports/review/overnight/`. Final repeat-check receipts and screenshots are in the
outside-worktree handoff directory; the delivered outside copy of this report is
`outputs/FIRETRACE_MORNING_REPORT.md` relative to the task workspace.

## Submission package decisions, 15 November 2026 Nepal time

- 2026-11-14 20:05 UTC: Keep seven authored slides, each title plus authored content within 40 words and notes within 60–90. Preserve real chart and screenshot labels separately as evidence; do not erase scientific labels to satisfy a literal OCR word count.
- 2026-11-14 20:07 UTC: Preserve exact source snapshots from the reviewed FRP and season branches, pin their source commits and hashes, and distinguish them from the deployed baseline. Repository visibility was checked with GitHub CLI and is PUBLIC; repeat public-link access checks before submission.
- 2026-11-14 20:08 UTC: The bundled presentation engine can export editable PPTX and render slides, but its native PDF exporter lacks a standard-font dependency. Produce the PDF from the same verified high-resolution slide renders using bundled ReportLab; no library installation or scientific-chart alteration is needed.
- 2026-11-14 20:10 UTC: Use NASA's current Global Organizing Team submission-field answer because the main guide URL returns HTTP 502. Leave registered team identity and the official project URL as explicit placeholders; no login, acceptance of terms or submission is performed.
- 2026-11-14 20:10 UTC: Real live evidence screenshots show the deployed baseline. The Nepal 2016 example is from training, and the India rhythm map is exploratory. Do not present these screenshots as validation of new branch results.
- 2026-11-14 20:10 UTC: Correct the judge explanation of uncertainty to match the app: daily conversion intervals are displayed separately, not summed into a weekly confidence interval. This is a documentation correction only.

## Final-night story review, 15 November 2026 Nepal time

- 2026-11-14 19:10 UTC: Work on the named feature branches and open reviewable PRs; preserve main at 290e756, the original UI backup, and the Workers migration worktree. Do not merge, deploy, log in, or rewrite history overnight.
- 2026-11-14 19:12 UTC: Treat the existing submission/ documents as the canonical slide, video, project-page, status and judge-Q&A paths; do not create duplicate root documents for names absent from this checkout.
- 2026-11-14 19:12 UTC: Describe rhythm as a separate analysis of original satellite streams, reproducing a known weekly pattern; do not imply harmonization discovered it or identified ignition causes.
- 2026-11-14 19:12 UTC: The India retrospective example compares the simple B1 conversion with selected M1, not raw VIIRS with conversion. Preserve its unmasked values and identify the pending common-date sensitivity separately; commit a reproduction script using the existing national sufficient statistics and frozen model.
- 2026-11-14 19:12 UTC: Use newly active grid cells for the recurrence proxy, not verified new ignitions; a nonsignificant country result does not establish absence of a pattern. Preserve every official number and gate decision.
- 2026-11-14 19:12 UTC: Distinguish NOAA-20 transfer corroboration from ground-truth validation, simulated power from exclusion of an effect, and calendar outage masking from unchanged model-evaluation and globe totals.
- 2026-11-14 19:12 UTC: The FRP contrast was already calculated before this overnight brief. Preserve the original timestamped protocol and hash; any new Git packaging commit must explicitly state that it follows the known result and cannot serve as a prior Git prediction.

- 2026-11-14 19:18 UTC: Independent review found residual overstatements in METHODS/LIMITATIONS and prior-timing language in README/slides; correct these in an additive follow-up commit, retain all numerical values, and rerun all checks. The initial build required sandbox escalation for esbuild file access; the same source built successfully without code changes.

- 2026-11-14 20:20 UTC: Preserve the original story-review section while moving it before scientific interpretation; mirror the corrected AI chronology and NOAA-20 transfer/coverage qualifications across story and submission, and synchronize the story season answer with the verified masked comparison. No scientific values, official decisions or historical protocol text change.

- 2026-11-14 20:23 UTC: Use historical S-NPP coverage and explicit daily calibration intervals in the story Q&A; describe the ranked regional table without a top-20-only restriction so root documentation remains accurate before and after the separately reviewed UI pagination. Scientific coverage values and frozen submission claims stay unchanged.

## Count versus FRP: overnight protocol receipt

Recorded 2026-11-14 19:21:16 UTC. **Chronology exception:** the preceding research session already calculated the FRP outcome. This Git receipt is retrospective packaging and does not predate that result. The original local protocol was frozen at 2026-11-14 18:57:23.284 UTC, before that session calculated the contrasts, with SHA-256 `1B88C8B3C7A1225FB2AA10E3B19DD9311CB7F4B022A9795C51552557BB434171`. Its preserved bytes and timestamp record accompany this branch. The outcome and criteria will not be changed to manufacture a fresh prediction or a prior Git record. This is not external preregistration or a new holdout.

The following protocol and prediction are copied word for word from the overnight brief; the later implementation is a reproducibility exercise of the completed test.

Protocol: United States, 2013-2024, vegetation (type 0), daytime only, the same confidence filters and IANA local civil time conversion as kill_test.py, Terra, Aqua and VIIRS S-NPP analysed separately. Use the cleaned caches or the raw FIRMS CSVs on this machine; reconcile detection counts against the official run and report any mismatch. Exclude outage dates from reports/review/OUTAGES.md, then repeat with the mask padded by 1 day on each side. FRP: keep only finite, non-negative values; missing is not zero.

Data gate: at least 95% valid FRP in every stream-year, and weekday missingness differing by no more than 1 percentage point within any stream-year. If the gate fails, stop and report it as failed.

Analysis: per year, compute exposure-adjusted weekday rates for (a) valid-FRP detection counts and (b) summed FRP; normalise each to its 7-day mean; Sunday delta = FRP index minus count index. Primary estimate: equal-weight mean of the 12 yearly deltas per stream. Bootstrap whole years 50,000 times, seed 20261115, using the same year draws for all streams; 98.33% intervals. Also report all 12 yearly deltas, leave-one-year-out means, and the result after removing each stream-year's single highest-FRP day from both metrics and their denominators.

Prediction: mean delta >= 0.05 with the interval wholly above zero in at least 2 of 3 streams, positive in every leave-one-year-out run and after removing the top-FRP day, under both outage masks.

Kill rule: if any condition fails, the test fails. Do not change the cutoff, switch to nighttime, Florida, other countries or other FRP definitions to rescue it.


- 2026-11-14 19:21:16 UTC: Retain the original, more explicit frozen conventions: the same two streams must pass both masks; intervals must exclude zero while the point estimate meets 0.05; exact tie-breaking, local-date masks and bootstrap draws remain fixed. No additional subgroup or new outcome is authorized.

- 2026-11-14 19:40 UTC: Publish the verified, fixed US daytime comparison only for the United States; retain Terra's failed interval criterion and the Git-after-results chronology in the visible panel.
- 2026-11-14 19:40 UTC: Require an independent receipt matching the current scripts and scientific artifacts before public export; preserve exact artifact bytes across Git checkout so line-ending conversion cannot invalidate hashes.
- 2026-11-14 19:40 UTC: Discover web test files through one shared runner so combining feature branches cannot silently omit either branch's tests; retain the existing three precheck suites.
- 2026-11-14 19:40 UTC: Desktop and 390-pixel browser checks passed for the new panel, its disclosure controls, country scope, and recovery after a missing payload. Existing page-wide phone overflow is assigned to the UI polish task; the FRP panel itself fits its container.

## Overnight UI decisions

- 2026-11-14 19:47 UTC: Move the existing scale control and its exact scope caption above the sidebar rather than introduce a second independent control; preserve readiness during link/data hydration.
- 2026-11-14 19:47 UTC: Fix the observed phone navigation overflow with two columns and improve scoped Rhythm readability without changing scientific text, values or caveats.
- 2026-11-14 19:47 UTC: Keep the existing independent rhythm-country picker and shared-URL schema; the requested deep link restores the tab, and broader state redesign exceeds this task.
- 2026-11-14 19:47 UTC: Reuse the FRP branch's identical web test discovery runner so merging the features cannot omit either suite. All real country/grid assets passed; no speculative data-path rewrite or new dataset is needed.

- 2026-11-14 20:20 UTC: During cross-PR review, relocate the unchanged UI decision section away from the shared end-of-file insertion point. Preserve every decision and all application code.

## Overnight season-preservation sensitivity

- 2026-11-14 19:55 UTC: Preserve the complete original retrospective scenario matrix and frozen models; rerun all seven countries and every original cut under the exact common 73-date mask and its 87-date padded sensitivity.
- 2026-11-14 19:55 UTC: Apply each mask to the same Aqua and VIIRS dates, retain monthly coverage counts, and describe count errors as agreement over retained dates rather than reconstructed full-year activity.
- 2026-11-14 19:55 UTC: Keep the January whole-year controls distinct from the February-to-December switch scenarios; report the India B1-to-M1 tradeoff and Nepal improvement descriptively, with no new significance or fresh-holdout claim.
- 2026-11-14 19:55 UTC: Preserve the all-country original summary under a distinct filename so it cannot collide with the separate India/Nepal reproduction fixture in story-wording; keep hash-pinned baseline bytes unchanged.

## Overnight integration and morning handoff

- 2026-11-14 20:40 UTC: Preserve the combined audit as an exported, exact-source simulation rather than merging any real branch. Record its source heads and tree separately from the old checkout commit reported by the legacy check helper.
- 2026-11-14 20:40 UTC: Resolve the morning Q&A conflicts in stages: corrected story questions 1–17 plus season Q18, followed by the final twenty-answer submission. Preserve the union of every DECISIONS section and the unchanged FRP protocol; no wholesale ours/theirs choice.
- 2026-11-14 20:40 UTC: Treat esbuild sandbox-read failures and archive line-ending conversion as environment/export issues, retaining failed receipts and using permission-only build retry or exact-byte export; do not change product code to hide them.
- 2026-11-14 20:40 UTC: Report the FRP task as partial against the impossible Git-before-result requirement, despite passing numerical/reproducibility gates. The old local protocol is evidence of local timing, not externally certified preregistration.
- 2026-11-14 20:40 UTC: Preserve the existing Rhythm-country/share-link limitations and large lazy-globe warning. Browser QA establishes the exercised flows, not a promise of universal faultlessness.
- 2026-11-14 20:40 UTC: Keep the frozen, reviewed briefing and twenty judge answers after a separate wording recheck found no material error. Leave genuine team identity and official project fields for the team, with no invented names or account actions.
- 2026-11-14 20:40 UTC: If morning time is short, UI polish is optional first; any smaller PR combination still needs its own validation. Do not present branch-only FRP/season evidence as already deployed or compromise story corrections to rush release.
- 2026-11-14 20:40 UTC: Re-run all five branch suites/builds once at their final source heads, then run submission checks again after the report commit. Publish only named feature branches and stop after the bounded handoff; no new analysis, feature, login, merge or deployment.
- 2026-11-14 20:40 UTC: Give the team exact PowerShell release commands with clean-tree/unpublished-commit stops, fast-forward-only pull, fresh pytest temporary/cache directories and final asset hashes. Run these only after approved morning merges, not as overnight actions.
- 2026-11-14 20:40 UTC: Use the supplied 14:00 feature freeze and 20:00 submission target, but require confirmation of any earlier local judging cutoff. Keep the seven-slide PDF as the ready demo option; the short script still needs an actual timed recording if used.
- 2026-11-14 20:42 UTC: Independent handoff reviewers confirmed the claims and requested precise calculation/receipt timestamp labels and a pre-deploy HEAD identity guard. Preserve copied audit bytes with scoped Git attributes; keep frozen source audit receipts unchanged.
