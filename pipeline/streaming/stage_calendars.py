"""Build review-only country calendars and measure the expanded static footprint."""
from pathlib import Path
import argparse
import gzip
import json
import time
import pandas as pd
from .aggregate_archives import write_json, peak_rss_bytes, ROOT
from pipeline import calendar


def build(converted, evaluation, rhythm_path, region_summary, output):
    converted, output = Path(converted),Path(output)
    output.mkdir(parents=True,exist_ok=True)
    conversion = json.loads((converted/"CONVERSION.json").read_text())
    summary = json.loads(Path(region_summary).read_text())
    if summary["archive_manifest_fingerprint"] != conversion["archive_manifest_fingerprint"]:
        raise ValueError("Region inventory and converted counts use different sources")
    evaluation = pd.read_csv(evaluation)
    rhythm = json.loads(Path(rhythm_path).read_text())
    regions = []
    started = time.monotonic()
    for item in conversion["files"]:
        daily = pd.read_parquet(converted/item["file"])
        regions.extend(calendar.build(daily,evaluation,rhythm,output,detections=None,label="REAL FIRMS DATA"))
        country = item["country"]
        path = output/f"{country}.json"
        payload = json.loads(path.read_text())
        total = summary["regions"][country]["occupied_cells_all_types"]
        payload["meta"]["cell_count_total"] = total
        payload["meta"]["model_revision"] = conversion.get("model_revision")
        count = payload["meta"]["cell_count_displayed"]
        payload["meta"]["cell_scope"] = f"{count} training-period-selected cells displayed out of {total} occupied cells; region total uses all cells."
        calendar.write_json(path,payload)
    index = json.loads((output/"index.json").read_text())
    index.update(regions=regions,phase="prepared-count pipeline",archive_manifest_fingerprint=conversion["archive_manifest_fingerprint"])
    index["model_revision"] = conversion.get("model_revision")
    calendar.write_json(output/"index.json",index)
    files = sorted(output.rglob("*"))
    files = [p for p in files if p.is_file()]
    totals, gzip_totals, listings = {},{},[]
    for path in files:
        category = "cell_json" if path.parent.name=="cells" else "globe_json" if path.name=="globe.json" else path.suffix.lstrip(".")
        size = path.stat().st_size
        gzip_size = len(gzip.compress(path.read_bytes(),compresslevel=9,mtime=0))
        totals[category] = totals.get(category,0)+size
        gzip_totals[category] = gzip_totals.get(category,0)+gzip_size
        listings.append({"file":str(path.relative_to(output)),"bytes":size,"lossless_gzip_bytes":gzip_size})
    shared_maps = [ROOT/"web/public/data/world-land.json",ROOT/"web/public/data/world-outline.json"]
    map_bytes = sum(p.stat().st_size for p in shared_maps if p.exists())
    dist = ROOT/"web/dist"
    assets = [p for p in dist.rglob("*") if p.is_file() and not str(p.relative_to(dist)).replace("\\","/").startswith("data/")]
    assets_bytes = sum(p.stat().st_size for p in assets)
    projected = sum(totals.values())+map_bytes+assets_bytes
    report = {"phase":"prepared-count payload build; no deployment","countries":len(regions),"data_files":len(files),
              "data_bytes":sum(totals.values()),"bytes_by_category":totals,"lossless_gzip_bytes_by_category":gzip_totals,
              "lossless_gzip_data_bytes":sum(gzip_totals.values()),"shared_map_bytes":map_bytes,"current_non_data_dist_bytes":assets_bytes,
              "projected_static_bytes":projected,"initial_budget_bytes":50*1024**2,"within_initial_budget":projected<=50*1024**2,
              "cloudflare_individual_limit_bytes":25*1024**2,"individual_files_within_limit":all(r["bytes"]<=25*1024**2 for r in listings),
              "largest_files":sorted(listings,key=lambda r:r["bytes"],reverse=True)[:12],
              "seconds":round(time.monotonic()-started,2),"peak_rss_bytes":peak_rss_bytes(),
              "scope_tradeoff":"Seven countries retain complete 2003–2024 daily national history, 12 daily cell series each, exports and all-cell annual globe. This expansion requires an explicit payload-budget decision before production.",
              "compression_note":"Gzip values are measurements only; compressed files are not substituted or served by this staging script."}
    write_json(output.parent/"PAYLOAD_BUDGET.json",report)
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--converted",required=True)
    parser.add_argument("--evaluation",required=True)
    parser.add_argument("--rhythm",required=True)
    parser.add_argument("--region-summary",required=True)
    parser.add_argument("--output",required=True)
    args = parser.parse_args()
    print(json.dumps(build(args.converted,args.evaluation,args.rhythm,args.region_summary,args.output),indent=2))
