# Overnight review evidence

These are preserved records of the five-branch integration rehearsal and two
independent consistency reviews. They describe the pinned heads in
`combined_validation.json`, before the documentation-only morning handoff commit.
They do not certify a real merge or deployment.

- `INTEGRATION_AUDIT.md`: source identity, conflicts, tests/build, preservation and limitations.
- `integration_receipt.json`: exact simulated stages and resolution provenance.
- `combined_validation.json`, `build_receipt.json`, `post_build_tree_check.json`: accepted combined validation.
- `pairwise_final.json`: pairwise conflicts; the chained merge's additional DECISIONS conflict is recorded separately in the integration receipt.
- `task6-science-audit.md` and its invariants/protected-results receipts: independent scientific wording and preservation review.
- `task6-frontend-audit.md`: independent source/slide review, separately attributed from the coordinator's browser checks.
- `DECISIONS.union.md`: exact original union used in the tested source tree; its SHA-256 matches the integration receipt.
- `DECISIONS.resolved.md`: that full union plus the later morning-handoff judgments. Use as a reviewed resolution reference, not an instruction to overwrite newer decisions blindly.
- `all_original_scientific_files.json`: byte/numeric preservation inventory.

The original working audit directory also contains the helper, temporary indexes,
archive, log files and preserved failed environment/export attempts. Those large
or machine-specific working artifacts are outside the repository at
`outputs/firetrace-integration-audit/` relative to the task workspace. Test receipts
are under `work/overnight/checks/`. Browser screenshots and the final delivery
receipt accompany the outside-worktree morning report. Paths in the frozen audit
records retain that workspace-relative meaning.

Use the root `MORNING_REPORT.md` for completed browser checks, task status,
scientific caveats, merge instructions and future release commands. Its appendices
retain all dated overnight decisions. After the team's actual merges, run all
tests and the asset verifier again on the resulting main commit.
