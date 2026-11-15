"""Extract submission facts from exact committed report snapshots; no new analysis.

Run with --write to create facts.json and SOURCE_LEDGER.md, or --check to verify
the packaged outputs without changing them. --audit-docs checks delivery limits.
Only the Python standard library is needed; no external worktrees are required.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
from pathlib import Path
import re

GROUPS = {
    "S01": ("Frozen harmonization choices", ["model", "selection"]),
    "S02": ("Layer 1 test results", ["layer1", "official_eval", "layer1_years"]),
    "S03": ("Ratio drift", ["ratio_trend", "layer1_years"]),
    "S04": ("Official weekly-rhythm rule", ["rhythm_gate", "rhythm_results"]),
    "S05": ("Rhythm review and Nepal simulation power", ["rhythm_review", "nepal_power"]),
    "S06": ("Newly active cells and imperfect controls", ["ignition_gate", "ignition_results", "controls", "volcano_controls"]),
    "S07": ("Exploratory northeast and failed Bangladesh prediction", ["northeast", "bangladesh_hills", "bangladesh_prediction"]),
    "S08": ("Outages and observation limits", ["outages", "methods", "product_readme", "limitations"]),
    "S09": ("NOAA-20 transfer check", ["noaa20_conversion", "noaa20_rhythm"]),
    "S10": ("Common-date season sensitivity", ["season_whole_year_comparison", "season_country_summary", "season_summary", "season_verification_independent_verification", "season_report"]),
    "S11": ("US daytime count-versus-FRP test", ["frp_summary", "frp_results", "frp_independent_verification", "frp_report", "frp_chart"]),
    "S12": ("Chronology and analysis decisions", ["decisions", "frp_protocol", "frp_independent_verification", "frp_source_snapshot", "season_source_snapshot", "ai_disclosure"]),
}


def encoded(value):
    return json.dumps(value, indent=2, allow_nan=False, ensure_ascii=False) + "\n"


def scalar(value):
    if value == "":
        return None
    if value in ("True", "False", "true", "false"):
        return value.lower() == "true"
    if re.fullmatch(r"-?\d+", value):
        return int(value)
    try:
        return float(value)
    except ValueError:
        return value


def extract(repo):
    evidence = repo / "submission/evidence"
    manifest = json.loads((evidence / "source_manifest.json").read_text(encoding="utf-8"))
    sources, values = {}, {}
    for source in manifest["sources"]:
        path = repo / source["local_path"]
        data = path.read_bytes()
        if hashlib.sha256(data).hexdigest() != source["sha256"]:
            raise ValueError(f"Snapshot hash mismatch: {source['local_path']}")
        sources[source["id"]] = source
        if path.suffix == ".csv":
            values[source["id"]] = [{k: scalar(v) for k, v in row.items()} for row in csv.DictReader(io.StringIO(data.decode("utf-8-sig")))]
        elif path.suffix == ".json":
            values[source["id"]] = json.loads(data)
    layer = values["layer1"]
    official = values["official_eval"]
    for row in layer:
        matches = [r for r in official if r["region"] == row["country"] and r["model"] == row["model"] and r["split"] == "test" and r["aggregation"] == "weekly"]
        if len(matches) != 1 or any(abs(float(matches[0][field]) - float(row[field])) > 1e-8 for field in ("bias_pct", "mae", "correlation")):
            raise ValueError("Layer 1 table no longer reproduces official locked evaluation")
    def layer_row(country, model):
        return next(r for r in layer if r["country"] == country and r["model"] == model)
    frp = values["frp_summary"]
    passed = sorted({r["stream"] for r in frp if r["mask"] == "primary" and r["pass"]}
                    & {r["stream"] for r in frp if r["mask"] == "padded" and r["pass"]})
    verification = values["frp_independent_verification"]
    if verification["status"] != "PASS" or sorted(verification["passing_streams_both_masks"]) != passed:
        raise ValueError("FRP summary is not consistent with independent verification")
    if values["season_verification_independent_verification"]["status"] != "PASS":
        raise ValueError("Season output lacks an independent passing receipt")
    frp_profiles = [dict(mask=r["mask"], stream=r["stream"], **r["mean_weekday_profiles"]) for r in values["frp_results"]["summaries"]]
    facts = dict(schema_version=1, purpose="Fact extraction only; no model fitting, statistical reanalysis or new scientific result.",
                 source_manifest_sha256=hashlib.sha256((evidence / "source_manifest.json").read_bytes()).hexdigest(),
                 source_ids=list(sources), source_groups={key: ids for key, (_, ids) in GROUPS.items()}, repository_access=manifest["repository_access"],
                 historical_disclosure_note="The exact historical AI disclosure snapshot is preserved as evidence. Its broad before-analysis sentence is qualified by current root AI_DISCLOSURE.md and JUDGE_QA question 9: no prior Git record of the first real-data gate run; FRP Git receipt came after the original outcome.",
                 harmonization=dict(train_years=values["model"]["fit_years"], validation_years=values["model"]["validation_years"],
                                    test_years=values["model"]["test_years"], selected_models={c: s["selected"] for c, s in values["model"]["selection"].items()},
                                    global_B1_ratio=values["model"]["ratios"]["B1"], layer1_rows=layer, yearly_rows=values["layer1_years"],
                                    ratio_trend=values["ratio_trend"], units="Aqua-reference-equivalent detections; weekly MAE is not percent error or number of fires."),
                 official_rhythm=dict(country_results=values["rhythm_gate"]["per_country"],
                                      all_detection_rows=[r for r in values["rhythm_results"] if r["subset"] == "all"],
                                      rule=values["rhythm_gate"]["rule"], caveats=values["rhythm_gate"]["caveats"]),
                 nepal_power=dict(rows=values["nepal_power"], meaning="Conditional planted-dip simulation on real volumes; not an observed effect or a causal result."),
                 ignition_robustness=dict(gate=values["ignition_gate"], rows=values["ignition_results"],
                                         meaning="Newly active grid cells are not verified ignitions; separate robustness outcome, not the official detection gate."),
                 controls=dict(rows=values["controls"], volcano_rows=values["volcano_controls"]),
                 exploratory_map=dict(northeast=values["northeast"], bangladesh_sunday_cells=values["bangladesh_hills"]),
                 outages=values["outages"], noaa20=dict(conversion_rows=values["noaa20_conversion"], rhythm_rows=values["noaa20_rhythm"],
                                                     meaning="A second VIIRS platform; no ground-truth validation. Strict common-date outage sensitivity remains outstanding."),
                 season=dict(whole_year_rows=values["season_whole_year_comparison"], country_rows=values["season_country_summary"],
                             directions=values["season_summary"]["direction_checks"], mask_sizes=values["season_summary"]["mask_sizes"],
                             meaning="Retrospective B1-versus-selected comparison, Aqua reference. Masked annual totals use retained dates; TV x100 is monthly-share disagreement in points."),
                 frp=dict(rows=frp, weekday_profiles=frp_profiles, passing_streams_both_masks=passed,
                          chronology=verification["chronology"], meaning="US daytime 2013–2024 vegetation detections; valid-FRP count and FRP indices use the same observations. Summed snapshot FRP is not energy, emissions, severity or cause."),
                 external_sourced_constants=manifest["external_sources"])
    facts["three_team_numbers"] = [
        dict(value=375, display="375 m", meaning="VIIRS nominal nadir active-fire product resolution", sources=["S13/modis_viirs_resolution"]),
        dict(value=layer_row("Nepal", "M1")["mae"], display=f"{layer_row('Nepal', 'M1')['mae']:.1f}",
             comparator_value=layer_row("Nepal", "B1")["mae"], comparator_display=f"{layer_row('Nepal', 'B1')['mae']:.1f}",
             meaning="Nepal selected weekly test MAE versus B1, Aqua-reference-equivalent detections", sources=["S02/layer1"]),
        dict(value=len(passed), total=len({r["stream"] for r in frp}), display=f"{len(passed)} of {len({r['stream'] for r in frp})}",
             meaning="FRP paired-contrast streams passing both masks; Aqua and S-NPP VIIRS pass, Terra does not", sources=["S11/frp_summary", "S11/frp_independent_verification"])]
    facts["display_claims"] = {
        "Nepal_weekly_MAE_B1": f"{layer_row('Nepal','B1')['mae']:.1f}",
        "Nepal_weekly_MAE_M1": f"{layer_row('Nepal','M1')['mae']:.1f}",
        "Egypt_selected_bias_pct": f"{layer_row('Egypt','M1')['bias_pct']:+.2f}",
        "FRP_passing_streams": passed,
        "India_season": [{"mask": r["mask"], "model": r["alternative"], "annual_error_percent": f"{100*r['mean_abs_annual_error']:.2f}",
                           "TV_points": f"{100*r['mean_tv']:.2f}"} for r in values["season_whole_year_comparison"] if r["country"] == "India" and r["alternative"] in ("B1", "selected")],
        "FRP_primary_indices": [{"stream": r["stream"], "count": f"{r['valid_count_sunday']:.3f}", "FRP": f"{r['frp_sunday']:.3f}",
                                 "delta": f"{r['mean_delta']:.3f}", "CI_lower": f"{r['ci_lower']:.3f}", "CI_upper": f"{r['ci_upper']:.3f}"} for r in frp if r["mask"] == "primary"]}
    return facts, sources, manifest["external_sources"]


def ledger(facts, sources, external):
    lines = ["# Submission source ledger", "", "Generated by `python scripts/build_submission_facts.py --write`; check with `--check`.", "",
             "This package extracts existing results. It performs no new scientific analysis. Exact source snapshots are pinned to Git commits and SHA-256 hashes in `source_manifest.json`; checks require no other branch or worktree.", "",
             f"Repository visibility was verified as PUBLIC by `gh repo view` (reported by the root reviewer; recorded {facts['repository_access']['recorded_utc']}). A final logged-out access check remains on the submission checklist. Local packaged snapshots are also available offline. Commands inside copied analysis reports refer to their pinned source branches; this branch independently reproduces fact extraction from their exact saved outputs.", ""]
    for key, (title, ids) in GROUPS.items():
        lines += [f"## {key}: {title}", ""]
        for source_id in ids:
            s = sources[source_id]
            relative = str(Path(s["local_path"]).relative_to("submission/evidence")).replace("\\", "/")
            lines += [f"- `{source_id}`: [{s['source_path']}]({s['source_url']}) · [exact snapshot]({relative}) · SHA-256 `{s['sha256']}`."]
        lines.append("")
    lines += ["## S13: External source constants", "", "These are attributed source statements, not values calculated from CINDERLINE data.", ""]
    for s in external:
        lines += [f"- `{s['id']}`: [source]({s['url']}); {s['retrieved_utc_date']} UTC; {s['verified_by']}. {s['interpretation']}"]
    lines += ["", "## Interpretation controls", "",
              "- Layer 1 weekly MAE, yearly error percentages and monthly-share TV measure different things. Keep their units and reference explicit.",
              "- The official all-detection weekly rhythm result differs from the US daytime FRP subset. Do not interchange their Sunday indices.",
              "- FRP succeeds in Aqua and S-NPP VIIRS under both masks; Terra's interval includes zero. It is an exploratory historical contrast, not proof of ignition cause, severity, emissions or fire size.",
              "- India and Nepal's season examples compare B1 with selected M1. Common masks do not create complete observation coverage or a new holdout.",
              "- The original local FRP protocol preceded its effects; the Git receipt followed the known outcome. The portable run is reproduction, not pre-analysis Git registration.",
              "- The exact historical AI disclosure snapshot retains its original broad before-analysis wording. Current root `AI_DISCLOSURE.md` and Judge Q&A question 9 supply the corrected chronology and take precedence for submission claims; preserving the source snapshot does not endorse the outdated sentence.",
              "- NOAA-20 supports platform transfer, not ground truth. Its strict common-date outage sensitivity remains pending.",
              "- Nepal's planted-dip figures are simulation results. A failed country test does not establish absence of human scheduling.",
              "- Brazil's stricter control fails, and the Bangladesh prediction fails; preserve these unfavorable results.", ""]
    return "\n".join(lines)


def words(text):
    # Count rendered link labels, not hidden URL destinations; numerals count.
    text = re.sub(r"!\[([^]]*)\]\([^)]*\)", r"\1", text)
    text = re.sub(r"\[([^]]+)\]\([^)]*\)", r"\1", text)
    text = re.sub(r"<https?://[^>]+>", "", text)
    return re.findall(r"[\w]+(?:[’'./:%+−-][\w]+)*", text, flags=re.UNICODE)


def audit_docs(repo):
    sub = repo / "submission"
    slide_text = (sub / "SLIDES.md").read_text(encoding="utf-8")
    matches = list(re.finditer(r"(?m)^##\s+(?:Slide\s+)?(\d+)\s*(?:[.:]|[—–-])\s+(.+)$", slide_text))
    blocks = [(match.group(2), slide_text[match.end():matches[i + 1].start() if i + 1 < len(matches) else len(slide_text)])
              for i, match in enumerate(matches)]
    checks, failures = [], []
    if len(blocks) != 7:
        failures.append(f"Expected exactly 7 slides, found {len(blocks)}")
    for number, (heading_title, block) in enumerate(blocks, 1):
        fields = dict((m.group(1).lower(), m.group(2).strip()) for m in re.finditer(
            r"\*\*(Title|On-slide|Visual|Speaker notes|Sources):\*\*\s*(.*?)(?=\n\*\*(?:Title|On-slide|Visual|Speaker notes|Sources):\*\*|\Z)", block, re.S))
        if not fields:
            fields = dict((m.group(1).lower().replace("on-slide text", "on-slide"), m.group(2).strip()) for m in re.finditer(
                r"(?m)^###\s+(On-slide text|Visual|Speaker notes|Sources)\s*\n(.*?)(?=^###\s+|\Z)", block, re.S))
            fields["title"] = heading_title
        if not all(key in fields for key in ("title", "on-slide", "visual", "speaker notes")):
            failures.append(f"Slide {number}: missing required labeled field")
        on_slide = len(words(fields.get("title", "") + " " + fields.get("on-slide", "")))
        notes = len(words(fields.get("speaker notes", "")))
        valid = on_slide <= 40 and 60 <= notes <= 90 and bool(fields.get("visual"))
        checks.append(dict(slide=number, title_and_slide_words=on_slide, speaker_note_words=notes, passed=valid))
        if not valid:
            failures.append(f"Slide {number}: slide={on_slide} words, notes={notes} words")
    project_count = len(words((sub / "PROJECT_PAGE.md").read_text(encoding="utf-8")))
    if project_count >= 500:
        failures.append(f"Project page must be under 500 words, found {project_count}")
    qa = (sub / "JUDGE_QA.md").read_text(encoding="utf-8")
    numbers = [int(n) for n in re.findall(r"(?m)^(?:\*\*|##\s+)(\d+)\.\s", qa)]
    if numbers != list(range(1, 21)):
        failures.append(f"Expected QA questions 1–20 exactly, found {numbers}")
    if "pending Task 4" in qa:
        failures.append("Judge QA still labels the completed season sensitivity as pending Task 4")
    doc_paths = {name: sub / name for name in ("SLIDES.md", "PROJECT_PAGE.md", "JUDGE_QA.md", "TEAM_BRIEFING.md", "VIDEO_SCRIPT.md", "SUBMISSION_CHECKLIST.md")}
    doc_paths["../AI_DISCLOSURE.md"] = repo / "AI_DISCLOSURE.md"
    doc_hashes = {name: hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest() for name, path in doc_paths.items() if path.exists()}
    return dict(status="PASS" if not failures else "FAIL", project_page_words=project_count, document_sha256_lf=doc_hashes,
                judge_question_numbers=numbers, slides=checks, failures=failures,
                scope="Delivery limits only. Scientific claims require source review; this is not a semantic fact-checker.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[1])
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check", action="store_true")
    parser.add_argument("--audit-docs", action="store_true")
    args = parser.parse_args()
    repo = args.repo_root.resolve()
    facts, sources, external = extract(repo)
    outputs = {"facts.json": encoded(facts), "SOURCE_LEDGER.md": ledger(facts, sources, external)}
    for name, content in outputs.items():
        path = repo / "submission/evidence" / name
        if args.write:
            path.write_text(content, encoding="utf-8", newline="\n")
        elif not path.exists() or path.read_text(encoding="utf-8") != content:
            raise SystemExit(f"Generated evidence differs: {name}; inspect sources, then run --write")
    print(f"PASS: {len(sources)} source hashes; Layer 1 official-table reconciliation; FRP/season verified receipts; deterministic fact extraction.")
    if args.audit_docs:
        report = audit_docs(repo)
        receipt_path = repo / "submission/evidence/document_checks.json"
        if args.write:
            receipt_path.write_text(encoded(report), encoding="utf-8", newline="\n")
        elif not receipt_path.exists() or json.loads(receipt_path.read_text(encoding="utf-8")) != report:
            raise SystemExit("Document checks or content changed since the saved receipt; review changes, then run --write --audit-docs")
        print(encoded(report))
        if report["status"] != "PASS":
            raise SystemExit(1)


if __name__ == "__main__":
    main()
