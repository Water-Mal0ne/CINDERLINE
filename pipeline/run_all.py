"""Reproduce FIRETRACE from public FIRMS archives or explicitly synthetic test data."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import shutil
import time

import pandas as pd

from pipeline import calendar, clean, download, harmonize, rhythm


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--download", action="store_true", help="Fetch/verify NASA annual archives first")
    parser.add_argument("--countries", nargs="+", default=["Nepal", "United_States"])
    parser.add_argument("--years", nargs=2, type=int, default=[2012, 2025])
    parser.add_argument("--raw-dir", default="data/raw")
    parser.add_argument("--clean-cache", default="data/processed/detections.parquet")
    parser.add_argument("--reuse-clean", action="store_true", help="Explicitly reuse existing cleaned parquet")
    parser.add_argument("--reuse-analysis", action="store_true", help="Reuse existing harmonization and rhythm reports")
    parser.add_argument("--synthetic", action="store_true", help="Separate synthetic fixtures/output, never presented as real")
    parser.add_argument("--max-cells", type=int, default=96)
    args = parser.parse_args()
    started = time.time()
    root = Path(__file__).resolve().parents[1]
    reports = root / ("reports/synthetic" if args.synthetic else "reports")
    processed = root / ("data/synthetic_processed" if args.synthetic else "data/processed")
    public = root / ("work/synthetic-web-data" if args.synthetic else "web/public/data")
    reports.mkdir(parents=True, exist_ok=True)
    processed.mkdir(parents=True, exist_ok=True)
    raw = root / args.raw_dir
    if args.synthetic:
        from pipeline.synthetic import generate
        detections = generate()
        manifest = detections.attrs.get("manifest", {})
        label = "SYNTHETIC DATA"
    else:
        if args.download:
            manifest = download.download(args.countries, range(args.years[0], args.years[1] + 1),
                                         data_dir=raw)
        else:
            manifest_path = raw / "manifest.json"
            if not manifest_path.exists():
                parser.error("No download manifest. Run with --download or use --synthetic for isolated tests.")
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        cache = root / args.clean_cache
        if args.reuse_clean and cache.exists():
            detections = pd.read_parquet(cache)
            print(f"Reusing cleaned cache: {len(detections):,} detections", flush=True)
        else:
            detections = clean.load_clean(raw)
            detections.to_parquet(cache, index=False)
        label = manifest.get("label", "UNVERIFIED INPUT")
    detections = detections[detections.country.isin(args.countries)].copy()
    detections.attrs.update(label=label, manifest=manifest)
    calendar.write_json(reports / "data_manifest.json", manifest)
    diagnostic_path = raw / "cleaning_diagnostics.json"
    if diagnostic_path.exists() and not args.synthetic:
        shutil.copyfile(diagnostic_path, reports / "cleaning_diagnostics.json")
    harmonized_path = processed / "harmonized.parquet"
    if args.reuse_analysis and harmonized_path.exists():
        daily = pd.read_parquet(harmonized_path)
        evaluation = pd.read_csv(reports / "harmonization_eval.csv")
        rhythm_result = json.loads((reports / "rhythm_results.json").read_text(encoding="utf-8"))
    else:
        print("Fitting reference-scale models and evaluating held-out years...", flush=True)
        daily, evaluation = harmonize.run(detections, reports)
        daily.to_parquet(harmonized_path, index=False)
        for region, rows in daily.groupby("region"):
            rows.to_parquet(processed / f"harmonized_{region}.parquet", index=False)
        print("Computing weekday estimates and release gate...", flush=True)
        rhythm_result = rhythm.run(detections, reports, label=label, manifest=manifest)
    from pipeline.synthetic import save_switch_check
    save_switch_check(reports)
    regions = calendar.build(daily, evaluation, rhythm_result, public, detections=detections,
                             label=label, max_cells=args.max_cells)
    summary = dict(label=label, regions=regions, detections=len(detections),
                   harmonized_rows=len(daily), rhythm_gate=rhythm_result["gate"]["decision"],
                   seconds=round(time.time() - started, 1),
                   web_data_bytes=sum(p.stat().st_size for p in public.glob("*")),
                   reused_clean=args.reuse_clean, reused_analysis=args.reuse_analysis)
    calendar.write_json(reports / "build_summary.json", summary)
    print(json.dumps(summary, indent=2), flush=True)


if __name__ == "__main__":
    main()
