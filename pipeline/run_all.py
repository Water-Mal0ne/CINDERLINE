"""Reproduce FIRETRACE from public FIRMS archives or explicitly synthetic test data."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import time

import pandas as pd

from pipeline import calendar, clean, download, harmonize, rhythm, rhythm_web


def manifest_signature(manifest, countries):
    """Fingerprint the actual inputs; local paths and transfer timestamps are irrelevant."""
    records = [{k: row.get(k) for k in ("country", "sensor", "year", "sha256", "complete", "status")}
               for row in manifest.get("files", []) if row.get("country") in countries]
    records.sort(key=lambda row: (row["country"], row["sensor"], row["year"]))
    return hashlib.sha256(json.dumps(records, sort_keys=True).encode()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--download", action="store_true", help="Fetch/verify NASA annual archives first")
    parser.add_argument("--countries", nargs="+", default=["Nepal", "United_States"])
    parser.add_argument("--years", nargs=2, type=int, default=[2002, 2025])
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
            cached_manifest = detections.attrs.get("manifest")
            if not cached_manifest or not cached_manifest.get("files"):
                parser.error("Cleaned cache lacks input provenance. Rebuild without --reuse-clean.")
            if manifest_signature(cached_manifest, args.countries) != manifest_signature(manifest, args.countries):
                print("Raw archives changed: --reuse-clean keeps the cached input snapshot; new archives are not included.", flush=True)
            manifest = cached_manifest
            print(f"Reusing cleaned cache: {len(detections):,} detections", flush=True)
        else:
            detections = clean.load_clean(raw)
            detections.to_parquet(cache, index=False)
        label = manifest.get("label", "UNVERIFIED INPUT")
    detections = detections[detections.country.isin(args.countries)].copy()
    absent = set(args.countries) - set(detections.country.unique())
    if absent:
        parser.error(f"Requested countries are absent from this cleaned input snapshot: {sorted(absent)}. Rebuild the cleaned data before including them.")
    detections.attrs.update(label=label, manifest=manifest)
    input_signature = manifest_signature(manifest, args.countries)
    analysis_signature = hashlib.sha256((input_signature + "".join(
        hashlib.sha256(Path(module.__file__).read_bytes()).hexdigest()
        for module in (harmonize, rhythm))).encode()).hexdigest()
    calendar.write_json(reports / "data_manifest.json", manifest)
    diagnostic_path = raw / "cleaning_diagnostics.json"
    if diagnostic_path.exists() and not args.synthetic:
        shutil.copyfile(diagnostic_path, reports / "cleaning_diagnostics.json")
    harmonized_path = processed / "harmonized.parquet"
    if args.reuse_analysis and harmonized_path.exists():
        summary_path = reports / "build_summary.json"
        previous = json.loads(summary_path.read_text()) if summary_path.exists() else {}
        if previous.get("analysis_signature") != analysis_signature:
            parser.error("Analysis cache does not match these inputs and analysis code. Re-run without --reuse-analysis.")
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
        # Official decision = pre-registered kill_test.py outputs; rhythm.py adds robustness checks only.
        official = None if args.synthetic else root / "reports/official"
        rhythm_result = rhythm.run(detections, reports, label=label, manifest=manifest, official=official)
    from pipeline.synthetic import save_switch_check
    save_switch_check(reports)
    regions = calendar.build(daily, evaluation, rhythm_result, public, detections=detections,
                             label=label, max_cells=args.max_cells)
    from pipeline import globe
    model_card = json.loads((reports / "harmonization_model.json").read_text(encoding="utf-8"))
    globe.build(detections, model_card, public / "globe.json")
    if not args.synthetic and (root / "reports/official/kill_test_gate.json").exists():
        rhythm_web.build(root / "reports/official", root / "reports/rhythm_robustness", public)
    summary = dict(label=label, regions=regions, detections=len(detections),
                   harmonized_rows=len(daily), rhythm_gate=rhythm_result["gate"]["decision"],
                   seconds=round(time.time() - started, 1),
                   web_data_bytes=sum(p.stat().st_size for p in public.rglob("*") if p.is_file()),
                   input_signature=input_signature, analysis_signature=analysis_signature,
                   reused_clean=args.reuse_clean, reused_analysis=args.reuse_analysis)
    calendar.write_json(reports / "build_summary.json", summary)
    print(json.dumps(summary, indent=2), flush=True)


if __name__ == "__main__":
    main()
