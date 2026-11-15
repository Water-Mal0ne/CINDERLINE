# Five-branch integration dry run

**PASS for the simulated combined source and automated checks. No real branch was
merged, reset, checked out, pushed or deployed by this audit.** Git references were
unchanged. Browser checks are being performed separately by the coordinator on
the same disposable snapshot.

## Exact source heads

| PR / branch | Tested commit |
|---|---|
| #5 `story-wording` | `ff4a64e8a78fdf6a1bb37dc3f0cb37a0bceaab2b` |
| #6 `frp-test` | `cf2f4d364fa8dc3fdd2e51108b4a76466f7f51c1` |
| #7 `ui-polish-v2` | `cb54eaca2f5a857cfe541dcb0509495413c2f120` |
| #8 `season-check` | `9ee15afe972cca97322ea371b1fdf3a66b45a0b6` |
| #9 `submission-final` | `e2568365ac6e0c7166ba305c2546177bded8917c` |

Baseline main: `290e7569ee1c7334f1161dc45daf4b02dc5c06ea`.
Final simulated tree: `d908acdbca8d5bf20a033f7cac77946636be59b3`.
Disposable source: `outputs/firetrace-integration-audit/combined/`.

`integration_receipt.json` binds every stage, resolution, source head and tree.
`build_snapshot.py` uses `git merge-tree`, a temporary index, unreferenced
`commit-tree` objects and an archive export. Those synthetic commits are test-only
objects and must not be pushed or used as real PR merge commits.

## Conflicts and actual merge guidance

The final ten pairwise checks show only `submission/JUDGE_QA.md` conflicts:
story/season, story/submission and season/submission. All application and
scientific-source combinations merge without conflicts. Earlier DECISIONS
collisions were reduced by the branches' documentation-only follow-ups; the
initial inventory is preserved separately.

Recommended sequence: **story → FRP → UI → season → submission**.

| Simulated stage | Result and resolution |
|---|---|
| Story + FRP | Clean automatic merge |
| + UI | Clean automatic merge |
| + season | QA conflict; the simulation chose the final complete twenty-answer QA as a final-tree convenience |
| + submission | DECISIONS conflict; preserved the union of all named decision sections from all five branches |

For the real intermediate season merge, **retain corrected story questions 1–17
and the exact season question 18**; story already contains the verified Q18
results. Do not revert to an older eighteen-answer file with stale uncertainty,
preregistration or S-NPP wording. The later submission merge deliberately replaces
that intermediate QA with the full final twenty answers. The test's early use of
the final QA does not imply that a real maintainer should pull submission changes
into the earlier season commit.

For the last DECISIONS conflict, retain the existing base timeline and all five
task sections. The exact audited union is `DECISIONS.union.md`; its heading
provenance is recorded in the receipt. No application change, model or scientific
result was selected by an ours/theirs shortcut.

## Automated checks

| Check | Result |
|---|---|
| Python tests | **81 passed** |
| Web tests | **45 passed**, with the three prechecks also retained |
| TypeScript and production build | **Passed** |
| Submission source and document guard | **Passed**, all 38 source hashes and current reviewed document hashes |
| Post-build source integrity | All **524 tracked files** still match the simulated tree exactly |
| Distribution | `index.html` exists; **126 files**, **52,271,113 bytes** |
| Largest asset | `globe.json`, **12,999,487 bytes**; no file exceeds **25 MiB** |

The first build attempt failed because the sandbox denied esbuild access to an
ancestor directory while resolving `vite.config.ts`. This was the same known
environment issue seen in individual branch checks. Python and web tests had
already passed. Only the build was retried with filesystem permission; it passed
without a source change or dependency installation. The build retains Vite's
existing large lazy-globe chunk warning; the globe remains a separate lazy chunk.

The first archive export also applied Windows CRLF conversion to unprotected text.
The exact-byte source guard caught it. That attempt is preserved under
`attempt-autocrlf/`; the accepted archive used per-command `core.autocrlf=false`.
No repository configuration or source file was changed to obtain the result.

Receipts:

- `work/overnight/checks/integration-final-945c6617a5df4186b48ca26a00358790/result.json`:
  Python/web passes and the first environment-only build failure.
- `build_receipt.json` and `build-escalated.log`: successful build-only retry.
- `post_build_tree_check.json`: exact tracked-source preservation.
- `pairwise_final.json` and `merge-*.txt`: actual collision inventory and stages.

The legacy check script required a Git directory to obtain a commit field, so it
used the original repository read-only with `GIT_WORK_TREE` pointed at the snapshot.
Its reported checkout commit is not the combined-source identity; use the pinned
source map and final tree above.

## Scientific and frontend preservation

All **15 original official result files** and **4 sample-data files** retain their
Git blobs exactly. Frozen models, selection, evaluation and lock files also match
main byte-for-byte. Of 113 original public-data files, 112 are unchanged; the
remaining `rhythm.json` contains exactly two intended story corrections:

- “absent” becomes “not established” in the headline.
- “new ignitions” becomes “newly active grid cells (not verified ignitions)”.

Every numeric leaf, key and array length in that payload is unchanged.
`frp.json` is a separate added dataset. Full details are in
`all_original_scientific_files.json`.

The independent frontend reviewer checked 28 owning-branch blobs, retained UI
controls and table accessibility, the US-only FRP mount, corrected story wording,
and the shared test runner. All six suites plus three prechecks remain present.
The coordinator's browser walkthrough supplements this source/test evidence.

This dry run establishes a reproducible candidate and known documentation
resolutions; it is not an assertion that the PRs have been merged or that the live
site contains their changes. Final merge resolutions should be checked again on
their actual resulting main commit before deployment.
