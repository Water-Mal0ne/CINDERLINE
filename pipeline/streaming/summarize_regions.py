"""Small exact inventory for calendar metadata without raw-record expansion."""
from pathlib import Path
import argparse
from collections import defaultdict
import json
import pandas as pd
from .aggregate_archives import write_json
from .prepare_analysis import input_snapshot
from pipeline.globe import manifest_fingerprint


def summarize(preparations, output):
    manifest,paths = input_snapshot(preparations)
    occupied, vegetation, totals, types = defaultdict(set),defaultdict(set),defaultdict(int),defaultdict(lambda:defaultdict(int))
    for path in paths:
        frame = pd.read_parquet(path,columns=["country","cell_id","type","n"])
        for country,group in frame.groupby("country",observed=True):
            occupied[country].update(group.cell_id.unique())
            vegetation[country].update(group.loc[group.type==0,"cell_id"].unique())
            totals[country] += int(group.n.sum())
            for fire_type,n in group.groupby("type",observed=True).n.sum().items():
                types[country][str(fire_type)] += int(n)
    report = {"phase":"prepared-count pipeline","archive_manifest_fingerprint":manifest_fingerprint(manifest),
              "scope":"All cleaned archived detections, including boundary/partial years; not a display-year fire total",
              "regions":{c:{"cleaned_detections":totals[c],"occupied_cells_all_types":len(occupied[c]),
                             "occupied_cells_vegetation_all_streams":len(vegetation[c]),"type_counts":dict(types[c])}
                         for c in sorted(totals)}}
    write_json(output,report)
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("preparations",nargs="+")
    parser.add_argument("--output",required=True)
    args = parser.parse_args()
    print(json.dumps(summarize(args.preparations,args.output),indent=2))
