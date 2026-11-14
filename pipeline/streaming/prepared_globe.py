"""Staged all-cell annual globe from exact stratum counts, one year at a time."""
from pathlib import Path
import argparse
import json
import time
import pandas as pd
from .aggregate_archives import peak_rss_bytes, write_json
from .prepared_runtime import read_inputs
from pipeline.harmonize import _archive_years, predict_counts
from pipeline.globe import manifest_fingerprint


def build_annual(analyses, model_path, output_path):
    started = time.monotonic()
    manifest, daily_paths, _ = read_inputs(analyses)
    model = json.loads(Path(model_path).read_text())
    fingerprint = manifest_fingerprint(manifest)
    if model["archive_manifest_fingerprint"] != fingerprint:
        raise ValueError("Locked model and annual count sources differ")
    carrier = pd.DataFrame()
    carrier.attrs["manifest"] = manifest
    regions = sorted(daily_paths)
    expected_annual = {}
    for country,path in daily_paths.items():
        summary = json.loads((path.parent/"ANALYSIS_INPUTS.json").read_text())
        expected_annual[country] = set(summary["annual_files"])
        for name in summary["annual_files"]:
            if not (path.parent/name).exists():
                raise ValueError(f"Missing declared annual partition: {path.parent/name}")
    availability = {c:{s:_archive_years(carrier,c,s) for s in ["Aqua","VIIRS"]} for c in regions}
    years = sorted(set().union(*(a["Aqua"]|a["VIIRS"] for a in availability.values())))
    size = float(model.get("grid_size",.25))
    output = {"years":years,"cell_size":size,"label":"REAL FIRMS DATA",
              "reference":"MODIS Aqua-equivalent archived detections","coverage_regions":[],"cells":[],
              "archive_manifest_fingerprint":fingerprint,"archive_files":len(manifest["files"]),
              "coverage_note":"Only listed regions have data. Zero means no qualifying archived detections, not observed absence of fire. Cloud/overpass coverage is unknown."}
    for country in regions:
        available = availability[country]
        eligible = available["Aqua"]|available["VIIRS"]
        sources = ["converted VIIRS" if y in available["VIIRS"] else "observed Aqua" if y in available["Aqua"] else "unavailable" for y in years]
        output["coverage_regions"].append({"id":country,"name":country.replace("_"," "),"sources":sources})
        values = {}
        for i,year in enumerate(years):
            if year not in eligible:
                continue
            stream = "VIIRS" if year in available["VIIRS"] else "Aqua"
            path = daily_paths[country].parent/f"annual_{country}_{year}.parquet"
            if path.name not in expected_annual[country]:
                continue  # Complete archive with no vegetation records produces zero cells.
            frame = pd.read_parquet(path)
            frame = frame[frame.stream==stream].copy()
            frame["value"] = predict_counts(frame,model["selection"][country]["selected"],model["ratios"]) if stream=="VIIRS" else frame.n.astype(float)
            totals = frame.groupby("cell_id",observed=True).value.sum()
            for cell,value in totals.items():
                if cell not in values:
                    values[cell] = [0. if y in eligible else None for y in years]
                values[cell][i] = float(value)
        for cell,series in sorted(values.items()):
            south,west = map(float,str(cell).split(":"))
            output["cells"].append({"id":f"{country}:{cell}","region":country,"lat":south+size/2,"lon":west+size/2,"values":series})
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True,exist_ok=True)
    output_path.write_text(json.dumps(output,separators=(",",":"),allow_nan=False),encoding="utf-8")
    write_json(output_path.with_suffix(".metrics.json"),{"cells":len(output["cells"]),"bytes":output_path.stat().st_size,
               "seconds":round(time.monotonic()-started,2),"peak_rss_bytes":peak_rss_bytes(),
               "archive_manifest_fingerprint":fingerprint,"phase":"prepared-count pipeline"})
    return output


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("analyses",nargs="+")
    parser.add_argument("--model",required=True)
    parser.add_argument("--output",required=True)
    args = parser.parse_args()
    payload = build_annual(args.analyses,args.model,args.output)
    print(json.dumps({"cells":len(payload["cells"]),"years":payload["years"],"archive_files":payload["archive_files"]}))
