"""
Export our cleaned 7-country detections in the column format FIRETRACE's pipeline/rhythm.py expects,
so its stricter checks can be run as ROBUSTNESS checks next to the official kill_test.py gate.

Usage: python export_rhythm_input.py [data_dir] OUT_DIR
Writes OUT_DIR/rhythm_input_7countries.parquet and OUT_DIR/rhythm_input_manifest.json.
Cleaning, confidence filter and local civil time are kill_test.py's own functions (imported, unchanged).
"""
import json
import os
import sys

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kill_test as kt  # noqa: E402


def main():
    data_dir = sys.argv[1] if len(sys.argv) > 2 else "data"
    out_dir = sys.argv[-1]
    os.makedirs(out_dir, exist_ok=True)
    veg, static = kt.clean(kt.load(data_dir))
    parts = []
    for frame, label in [(veg, "vegetation"), (static, "static_control")]:
        f = kt.add_local_time(frame, label)
        cols = {"country": f["country"].astype(str), "stream": f["stream"].astype(str),
                "type": f["type"].fillna(0).astype("int8"), "local_date": f["local"].dt.normalize(),
                "daynight": f["daynight"].astype(str)}
        parts.append(pd.DataFrame(cols))
        del f
    del veg, static
    out = pd.concat(parts, ignore_index=True)
    for c in ["country", "stream", "daynight"]:
        out[c] = out[c].astype("category")
    out.to_parquet(os.path.join(out_dir, "rhythm_input_7countries.parquet"), index=False)

    # Manifest in FIRETRACE downloader format: one entry per annual archive actually present.
    files = []
    for sensor in ["modis", "viirs-snpp"]:
        for year in sorted(os.listdir(os.path.join(data_dir, sensor))):
            for name in sorted(os.listdir(os.path.join(data_dir, sensor, year))):
                if not name.endswith(".csv"):
                    continue
                country = name[:-4].split("_", 2)[2]
                files.append({"country": country, "sensor": sensor, "year": int(year),
                              "url": f"https://firms.modaps.eosdis.nasa.gov/data/country/{sensor}/{year}/{name}",
                              "status": "complete", "complete": True,
                              "coverage_start": f"{year}-01-01T00:00:00Z",
                              "coverage_end": f"{int(year) + 1}-01-01T00:00:00Z",
                              "completeness_basis": "Annual archive present locally; satellite coverage unknown"})
    manifest = {"label": "REAL FIRMS DATA", "source": "https://firms.modaps.eosdis.nasa.gov/data/country",
                "observation_coverage": "unknown", "files": files}
    with open(os.path.join(out_dir, "rhythm_input_manifest.json"), "w") as fh:
        json.dump(manifest, fh, indent=1)
    print(f"rows {len(out):,}; archives {len(files)}; diagnostics {json.dumps(kt.diag)}")


if __name__ == "__main__":
    main()
