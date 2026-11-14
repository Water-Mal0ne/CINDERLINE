"""
EXPLORATORY: northeast India follow-ups after review (tasks C1-C3). Official results unchanged.

python ne_india_review.py data rhythm_cells.csv ADMIN1_GEOJSON OUT_DIR

C2  Land share of each India VIIRS cell (rhythm_map.py cells) inside India and inside each Indian state, from a 25 x 25
    grid of sample points per 1-degree cell tested against Natural Earth admin-1 polygons. A cell is "mostly inside
    India" if >= 50% of its land sample points fall in India. Cross-border cells are listed separately.
C3  For cells whose largest Indian-state share is Assam: Assam share vs neighbouring hill-state shares, and the Sunday
    index for cells that are mostly (>= 50% of land) Assam.
C1  Year-by-year Sunday index (per-year rate / mean rate, kill_test.py method) for cells mostly inside India whose
    largest state share is Nagaland, Mizoram or Manipur, pooled, VIIRS and Aqua.
"""
import json
import os
import sys

import numpy as np
import pandas as pd
from matplotlib.path import Path as MplPath

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kill_test as kt  # noqa: E402
import rhythm_map as rm  # noqa: E402

LABEL = "REAL FIRMS DATA, VIIRS S-NPP 2013-2024 (EXPLORATORY)"
HILL = ["Nagaland", "Mizoram", "Manipur"]
NE = ["Arunachal Pradesh", "Assam", "Manipur", "Meghalaya", "Mizoram", "Nagaland", "Tripura"]
N_SAMPLE = 25


def polys(feature):
    g = feature["geometry"]
    ps = [g["coordinates"]] if g["type"] == "Polygon" else g["coordinates"]
    return [[np.asarray(r) for r in p] for p in ps]


def inside(paths, pts):
    hit = np.zeros(len(pts), bool)
    for outer, holes in paths:
        m = outer.contains_points(pts)
        for h in holes:
            m &= ~h.contains_points(pts)
        hit |= m
    return hit


def main():
    data_dir, cells_csv, admin1, out = sys.argv[1:5]
    os.makedirs(out, exist_ok=True)
    gj = json.load(open(admin1, encoding="utf-8"))
    by_name, land = {}, []
    for f in gj["features"]:
        p = f["properties"]
        paths = [(MplPath(pp[0]), [MplPath(h) for h in pp[1:]]) for pp in polys(f)]
        land.extend(paths)
        if p.get("adm0_a3") == "IND":
            by_name[p["name"]] = paths
    cells = pd.read_csv(cells_csv)
    india = cells[(cells.country == "India") & (cells.stream == "VIIRS")].copy()
    aqua = cells[(cells.country == "India") & (cells.stream == "Aqua")].set_index(["cell_lat", "cell_lon"])
    offs = (np.arange(N_SAMPLE) + 0.5) / N_SAMPLE
    rows = []
    for c in india.itertuples():
        pts = np.array([(c.cell_lon + x, c.cell_lat + y) for y in offs for x in offs])
        shares = {}
        for name, paths in by_name.items():
            near = any(p[0].get_extents().x0 <= c.cell_lon + 1 and p[0].get_extents().x1 >= c.cell_lon and
                       p[0].get_extents().y0 <= c.cell_lat + 1 and p[0].get_extents().y1 >= c.cell_lat for p in paths)
            if near:
                k = inside(paths, pts).mean()
                if k > 0:
                    shares[name] = k
        india_share = sum(shares.values())
        top = max(shares, key=shares.get) if shares else None
        rows.append({"cell_lat": c.cell_lat, "cell_lon": c.cell_lon, "india_share_of_cell": round(india_share, 3),
                     "largest_state": top, "largest_state_share": round(shares.get(top, 0), 3),
                     "state_shares": json.dumps({k: round(v, 3) for k, v in sorted(shares.items(), key=lambda kv: -kv[1])}),
                     "rest_index": c.rest_index, "ci_lo": c.ci_lo, "ci_hi": c.ci_hi, "q_bh": c.q_bh,
                     "significant": c.significant,
                     "aqua_rest_index": aqua.rest_index.get((c.cell_lat, c.cell_lon), np.nan),
                     "aqua_significant": aqua.significant.get((c.cell_lat, c.cell_lon), np.nan)})
    t = pd.DataFrame(rows)
    # India share is of the whole cell (sea counts as outside). "Mostly inside India" uses the share of the cell's
    # land: India share / land share, with land = any admin-1 polygon of any country.
    land_share = []
    for c in t.itertuples():
        pts = np.array([(c.cell_lon + x, c.cell_lat + y) for y in offs for x in offs])
        near = [p for p in land if p[0].get_extents().x0 <= c.cell_lon + 1 and p[0].get_extents().x1 >= c.cell_lon
                and p[0].get_extents().y0 <= c.cell_lat + 1 and p[0].get_extents().y1 >= c.cell_lat]
        land_share.append(inside(near, pts).mean() if near else 0)
    t["land_share_of_cell"] = np.round(land_share, 3)
    t["india_share_of_land"] = np.where(t.land_share_of_cell > 0, (t.india_share_of_cell / t.land_share_of_cell).round(3), np.nan)
    t["mostly_india"] = t.india_share_of_land >= 0.5
    t["northeast"] = t.cell_lon >= 89
    t.insert(0, "label", LABEL)
    t.to_csv(os.path.join(out, "c2_india_cells_area_shares.csv"), index=False)

    ne = t[t.northeast]
    inside_ne, cross = ne[ne.mostly_india], ne[~ne.mostly_india]
    rest = t[(~t.northeast) & t.mostly_india]
    summary = {
        "northeast_cells_tested": int(len(ne)),
        "northeast_mostly_india": {"cells": int(len(inside_ne)), "significant": int(inside_ne.significant.sum()),
                                   "median_sunday_index": round(float(inside_ne.rest_index.median()), 3)},
        "northeast_cross_border": {"cells": int(len(cross)), "significant": int(cross.significant.sum()),
                                   "median_sunday_index": round(float(cross.rest_index.median()), 3) if len(cross) else None},
        "rest_of_india_mostly_india": {"cells": int(len(rest)), "significant": int(rest.significant.sum()),
                                       "median_sunday_index": round(float(rest.rest_index.median()), 3)},
        "india_cells_not_mostly_india_outside_northeast": int(((~t.northeast) & (~t.mostly_india)).sum()),
    }
    # C3 Assam
    assam = ne[ne.largest_state == "Assam"].copy()
    assam["assam_share_of_india_part"] = [json.loads(s).get("Assam", 0) / max(i, 1e-9)
                                          for s, i in zip(assam.state_shares, assam.india_share_of_cell)]
    assam["hill_state_share_of_india_part"] = [sum(v for k, v in json.loads(s).items() if k in NE and k != "Assam") / max(i, 1e-9)
                                               for s, i in zip(assam.state_shares, assam.india_share_of_cell)]
    mostly_assam = assam[assam.assam_share_of_india_part >= 0.5]
    summary["assam_cells"] = {"cells": int(len(assam)), "mostly_assam_cells": int(len(mostly_assam)),
                              "mostly_assam_significant": int(mostly_assam.significant.sum()),
                              "mostly_assam_median_sunday_index": round(float(mostly_assam.rest_index.median()), 3) if len(mostly_assam) else None}
    assam.to_csv(os.path.join(out, "c3_assam_cells.csv"), index=False)

    # C1 yearly index for Nagaland/Mizoram/Manipur cells mostly inside India
    hill = inside_ne[inside_ne.largest_state.isin(HILL)]
    keys = set(zip(hill.cell_lat, hill.cell_lon))
    veg, _ = kt.clean(rm.load(data_dir, ["India"]))
    veg = veg[veg.stream.isin(["VIIRS", "Aqua"]) & (veg.longitude >= 89)]
    veg = kt.add_local_time(veg, "vegetation")
    veg = veg[[k in keys for k in zip(np.floor(veg.latitude).astype(int), np.floor(veg.longitude).astype(int))]]
    sun = kt.DAYS.index("Sun")
    yr_rows = []
    for stream in ["VIIRS", "Aqua"]:
        sub = veg[veg.stream == stream]
        for year, y in sub.groupby("year"):
            year = int(year)
            if year >= 2025 or (y.file_year == year).mean() < 0.95:
                continue
            rate = np.bincount(y.weekday.astype(int), minlength=7) / kt.weekday_exposure(year)
            idx = rate / rate.mean()
            yr_rows.append({"stream": stream, "year": year, "detections": int(len(y)), "sunday_index": round(float(idx[sun]), 3),
                            "lowest_day": kt.DAYS[int(idx.argmin())]})
    yt = pd.DataFrame(yr_rows)
    yt.insert(0, "label", LABEL)
    yt.to_csv(os.path.join(out, "c1_hill_states_yearly.csv"), index=False)
    summary["hill_cells_used"] = sorted([f"{a}N {b}E ({s})" for a, b, s in zip(hill.cell_lat, hill.cell_lon, hill.largest_state)])
    for stream in ["VIIRS", "Aqua"]:
        s = yt[yt.stream == stream]
        summary[f"hill_{stream}_years_below_1"] = f"{int((s.sunday_index < 1).sum())} of {len(s)}"
        summary[f"hill_{stream}_min_max"] = [float(s.sunday_index.min()), float(s.sunday_index.max())]
    json.dump(summary, open(os.path.join(out, "c_summary.json"), "w"), indent=2)
    print(json.dumps(summary, indent=2))
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(8, 4.2))
    for stream, color in [("VIIRS", "#e8590c"), ("Aqua", "#1c7ed6")]:
        s = yt[yt.stream == stream]
        ax.plot(s.year, s.sunday_index, marker="o", color=color, label=stream)
    ax.axhline(1, color="black", lw=0.7)
    ax.set_ylim(0, max(1.3, yt.sunday_index.max() + 0.1))
    ax.set_ylabel("Sunday index (1.0 = average day)")
    ax.set_title(f"[{LABEL}]\nNagaland, Mizoram and Manipur cells (mostly inside India), Sunday index by year", fontsize=9)
    ax.legend()
    fig.tight_layout()
    fig.savefig(os.path.join(out, "c1_hill_states_yearly.png"), dpi=130)


if __name__ == "__main__":
    main()
