"""
EXPLORATORY (review E9): where the US Sunday dip is strongest and weakest. Numbers only, no causal claims.

python us_cell_regions.py rhythm_cells.csv ADMIN1_GEOJSON OUT_DIR

Each US 1-degree VIIRS cell from rhythm_map.py is assigned to the state containing the largest share of a 25 x 25 grid
of sample points (Natural Earth admin-1), then to a region group fixed here before looking at the per-region numbers.
"""
import json
import os
import sys

import numpy as np
import pandas as pd
from matplotlib.path import Path as MplPath

GROUPS = {
    "Southeast": ["Alabama", "Arkansas", "Florida", "Georgia", "Louisiana", "Mississippi", "South Carolina",
                  "North Carolina", "Tennessee", "Kentucky", "Virginia"],
    "Southern Plains": ["Texas", "Oklahoma", "Kansas", "Nebraska", "Missouri"],
    "Northern Plains and Midwest": ["North Dakota", "South Dakota", "Minnesota", "Iowa", "Wisconsin", "Illinois",
                                    "Indiana", "Michigan", "Ohio"],
    "Pacific coast": ["California", "Oregon", "Washington"],
    "Interior West": ["Idaho", "Montana", "Wyoming", "Nevada", "Utah", "Colorado", "Arizona", "New Mexico"],
    "Northeast": ["Pennsylvania", "New York", "New Jersey", "Maryland", "Delaware", "West Virginia", "Connecticut",
                  "Massachusetts", "Vermont", "New Hampshire", "Maine", "Rhode Island", "District of Columbia"],
    "Alaska and Hawaii": ["Alaska", "Hawaii"],
}
STATE_GROUP = {s: g for g, ss in GROUPS.items() for s in ss}
N = 25


def main():
    cells_csv, admin1, out = sys.argv[1:4]
    os.makedirs(out, exist_ok=True)
    gj = json.load(open(admin1, encoding="utf-8"))
    states = {}
    for f in gj["features"]:
        if f["properties"].get("adm0_a3") != "USA":
            continue
        g = f["geometry"]
        ps = [g["coordinates"]] if g["type"] == "Polygon" else g["coordinates"]
        states[f["properties"]["name"]] = [(MplPath(np.asarray(p[0])), [MplPath(np.asarray(h)) for h in p[1:]]) for p in ps]
    c = pd.read_csv(cells_csv)
    us = c[(c.country == "United_States") & (c.stream == "VIIRS")].copy()
    offs = (np.arange(N) + 0.5) / N
    best = []
    for r in us.itertuples():
        pts = np.array([(r.cell_lon + x, r.cell_lat + y) for y in offs for x in offs])
        shares = {}
        for name, paths in states.items():
            if not any(p[0].get_extents().x0 <= r.cell_lon + 1 and p[0].get_extents().x1 >= r.cell_lon and
                       p[0].get_extents().y0 <= r.cell_lat + 1 and p[0].get_extents().y1 >= r.cell_lat for p in paths):
                continue
            hit = np.zeros(len(pts), bool)
            for outer, holes in paths:
                m = outer.contains_points(pts)
                for h in holes:
                    m &= ~h.contains_points(pts)
                hit |= m
            if hit.any():
                shares[name] = hit.mean()
        best.append(max(shares, key=shares.get) if shares else None)
    us["state"] = best
    us["region"] = us.state.map(STATE_GROUP).fillna("unassigned")
    us.to_csv(os.path.join(out, "e9_us_cells_by_state.csv"), index=False)
    rows = []
    for region, g in us.groupby("region"):
        rows.append({"region": region, "cells": len(g), "significant": int(g.significant.sum()),
                     "share_significant": round(g.significant.mean(), 3),
                     "median_sunday_index": round(g.rest_index.median(), 3),
                     "min_sunday_index": round(g.rest_index.min(), 3), "max_sunday_index": round(g.rest_index.max(), 3),
                     "median_detections_per_year": round(g.mean_detections_per_year.median(), 1)})
    reg = pd.DataFrame(rows).sort_values("median_sunday_index")
    reg.insert(0, "label", "REAL FIRMS DATA, VIIRS S-NPP 2013-2024 (EXPLORATORY)")
    reg.to_csv(os.path.join(out, "e9_us_regions.csv"), index=False)
    st = us.groupby("state").agg(cells=("rest_index", "size"), significant=("significant", "sum"),
                                 median_sunday_index=("rest_index", "median")).round(3)
    st = st[st.cells >= 3].sort_values("median_sunday_index")
    st.to_csv(os.path.join(out, "e9_us_states_3plus_cells.csv"))
    pd.set_option("display.width", 200)
    print(reg.drop(columns=["label"]).to_string(index=False))
    print("\nStates with >= 3 cells, strongest and weakest:\n" + pd.concat([st.head(6), st.tail(6)]).to_string())


if __name__ == "__main__":
    main()
