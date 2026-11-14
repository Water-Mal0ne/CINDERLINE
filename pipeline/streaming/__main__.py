"""Reproducible exact-count preparation and static-data builds."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

import pandas as pd
from .aggregate_archives import prepare, write_json, ROOT
from .prepare_analysis import build as reduce_counts, input_snapshot
from .evaluate_counts import evaluate, load_locked_evaluation, seal_locked_artifacts
from .prepared_runtime import read_inputs, run_preaggregated
from .prepared_globe import build_annual
from .weighted_rhythm import run_counts
from .summarize_regions import summarize
from .stage_calendars import build as build_calendars
from .estimate_dictionary import estimate as encode_public
from ..globe import manifest_fingerprint
from ..download import COUNTRIES


def require_complete_history(manifest, expected_countries=None):
    countries = sorted({r["country"] for r in manifest["files"]})
    if expected_countries is not None and set(countries)!=set(expected_countries):
        raise ValueError(f"Country scope differs: input={countries}, expected={sorted(expected_countries)}")
    valid = set()
    for row in manifest["files"]:
        year = int(row["year"])
        if (row.get("complete") is True and row.get("status")=="complete" and row.get("sha256")
            and str(row.get("coverage_start","")).startswith(f"{year}-01-01")
            and str(row.get("coverage_end","")).startswith(f"{year+1}-01-01")):
            valid.add((row["country"],row["sensor"],year))
    required = {(c,s,y) for c in countries for s,first in [("modis",2002),("viirs-snpp",2012)] for y in range(first,2026)}
    missing = required-valid
    if missing:
        raise ValueError(f"The 2003–2024 display requires complete bracketing archives; missing {sorted(missing)[:8]}")
    return countries


def additional_reports(preparations, analyses, model_path, output, reports):
    """Reproduce controlled-switch and prespecified supplemental checks separately."""
    from ..synthetic import save_switch_check
    save_switch_check(reports)
    subprocess.run([sys.executable,"-m","pipeline.validation.science_checks",
                    "--preparations",*map(str,preparations),"--analyses",*map(str,analyses),
                    "--model",str(Path(model_path).resolve()),"--output",str(Path(output).resolve())],
                   cwd=ROOT,check=True)


def build(args):
    manifest,_ = input_snapshot(args.preparations)
    countries = require_complete_history(manifest,args.expected_countries)
    if args.analyses:
        analysis_manifest,_,_ = read_inputs(args.analyses)
        if manifest_fingerprint(analysis_manifest)!=manifest_fingerprint(manifest):
            raise ValueError("Prepared counts and analysis tables have different source snapshots")
    output = Path(args.output)
    if output.exists():
        raise ValueError("Use a fresh output directory; prior builds and locked selections are preserved")
    output.mkdir(parents=True)
    baseline = {}
    if args.baseline_reports:
        origin = Path(args.baseline_reports)
        destination = output/"baseline"
        destination.mkdir()
        for name in ["harmonization_model.json","harmonization_eval.csv","rhythm_results.json","kill_test_gate.json"]:
            path = origin/name
            if path.exists():
                shutil.copyfile(path,destination/name)
                baseline[name] = hashlib.sha256(path.read_bytes()).hexdigest()
        write_json(destination/"snapshot.json",{"source":str(origin.resolve()),"sha256":baseline})
    analyses = args.analyses or []
    if not analyses:
        for i,preparation in enumerate(args.preparations):
            target = output/"analysis"/str(i)
            reduce_counts([preparation],target)
            analyses.append(str(target))
    reports = output/"reports"
    model = load_locked_evaluation(analyses,args.locked_evaluation,reports) if args.locked_evaluation else evaluate(analyses,reports)
    model.update(label="REAL FIRMS DATA",model_revision=args.model_revision or f"{len(countries)}-country-{manifest_fingerprint(manifest)[:12]}",
                 calibration_countries=countries,baseline_report_sha256=baseline,grid_size=.25,map_cells=12,
                 baseline_commit=args.baseline_commit,
                 uncertainty="95% training-year bootstrap calibration interval; not total observation/prediction uncertainty",
                 revision_note="Global training ratio is refitted for the declared country scope; validation selection is unchanged and locked before test evaluation.")
    write_json(reports/"harmonization_model.json",model)
    seal_locked_artifacts(reports)
    write_json(reports/"data_manifest.json",manifest)
    if args.science_checks:
        additional_reports(args.preparations,analyses,reports/"harmonization_model.json",output/"scientific_validation",reports)
    else:
        from ..synthetic import save_switch_check
        save_switch_check(reports)
    converted = output/"processed"
    conversion = run_preaggregated(analyses,reports/"harmonization_model.json",converted)
    counts = pd.concat([pd.read_parquet(Path(p)/"rhythm_counts.parquet") for p in args.preparations],ignore_index=True)
    rhythm = run_counts(counts,manifest,reports)
    summarize(args.preparations,reports/"regions.json")
    original = output/"public_original/data"
    globe = build_annual(analyses,reports/"harmonization_model.json",original/"globe.json")
    raw_budget = build_calendars(converted,reports/"harmonization_eval.csv",reports/"rhythm_results.json",reports/"regions.json",original)
    public = output/"public/data"
    if args.no_encode:
        shutil.copytree(original,public)
        budget = raw_budget
    else:
        budget = encode_public(original,public)
    for name in ["world-land.json","world-outline.json"]:
        source = ROOT/"web/public/data"/name
        if source.exists():
            shutil.copyfile(source,public/name)
    summary = {"label":"REAL FIRMS DATA","countries":countries,"model_revision":model["model_revision"],
               "archive_files":len(manifest["files"]),"archive_manifest_fingerprint":manifest_fingerprint(manifest),
               "cleaned_detections":int(counts.n.sum()),"daily_rows":sum(r["rows"] for r in conversion["files"]),
               "globe_cells":len(globe["cells"]),"gate":rhythm["gate"]["decision"],
               "projected_static_bytes":budget["projected_static_bytes"],"within_initial_budget":budget["within_initial_budget"],
               "publication":"Generated locally; production payloads and deployment are unchanged."}
    write_json(output/"BUILD.json",summary)
    print(json.dumps(summary,indent=2))
    return 0 if summary["within_initial_budget"] else 2


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command",required=True)
    p = commands.add_parser("prepare",help="Verify and clean annual archives in bounded chunks")
    p.add_argument("--manifest",required=True)
    p.add_argument("--countries",nargs="+",required=True)
    p.add_argument("--output",required=True)
    p.add_argument("--chunk-size",type=int,default=200000)
    p.add_argument("--write-clean",action="store_true")
    b = commands.add_parser("build",help="Lock, evaluate and build public data from completed preparations")
    b.add_argument("--preparations",nargs="+",required=True)
    b.add_argument("--analyses",nargs="+",help="Optional previously verified reductions with matching manifests")
    b.add_argument("--output",required=True)
    b.add_argument("--baseline-reports")
    b.add_argument("--locked-evaluation",help="Reuse a hash-verified evaluation directory without rerunning selection or held-out evaluation")
    b.add_argument("--model-revision",help="Explicit revision label, e.g. seven-country-v1")
    b.add_argument("--baseline-commit",help="Recorded prior-release commit identifier")
    b.add_argument("--science-checks",action="store_true",help="Also reproduce the prespecified grid/bridge validation; reproduce includes this automatically")
    b.add_argument("--expected-countries",nargs="+")
    b.add_argument("--no-encode",action="store_true",help="Keep the original payload format; oversized builds return exit code 2")
    r = commands.add_parser("reproduce",help="Download official archives, prepare counts, and build an isolated full website; never deploy")
    r.add_argument("--output",required=True,help="A fresh directory for all reproduction artifacts")
    r.add_argument("--countries",nargs="+",choices=COUNTRIES,default=COUNTRIES)
    r.add_argument("--source-manifest",help="Reuse existing verified archive paths instead of downloading")
    r.add_argument("--workers",type=int,choices=[1,2,3,4],default=3)
    r.add_argument("--chunk-size",type=int,default=200000)
    r.add_argument("--locked-evaluation",help="Reuse hashed saved choices/evaluation rather than recomputing selection/test")
    r.add_argument("--baseline-reports")
    r.add_argument("--model-revision")
    r.add_argument("--baseline-commit")
    args = parser.parse_args()
    if args.command=="prepare":
        result = prepare(args.manifest,args.countries,args.output,args.chunk_size,args.write_clean)
        print(json.dumps({k:v for k,v in result.items() if k not in ["archives","contract"]},indent=2))
        return 0
    if args.command=="reproduce":
        from .reproduce import reproduce
        return reproduce(args,build_fn=build)
    return build(args)


if __name__ == "__main__":
    raise SystemExit(main())
