"""
EXPLORATORY: northeast India per-state breakdown of the Sunday dip (not part of the pre-specified test).

python ne_india_states.py data rhythm_cells.csv ADMIN1_GEOJSON OUT_DIR

- Takes the India VIIRS cells analysed by rhythm_map.py east of 89 E (the "northeast India" area).
- Assigns each cell to a state by its centroid (cell_lat + 0.5, cell_lon + 0.5), using Natural Earth
  admin-1 boundaries (ne_10m_admin_1_states_provinces). Centroids outside every Indian state are
  reported as unassigned, with the country the centroid falls in.
- Per state: cells, BH-significant cells, median cell Sunday index, and a state-level weekday index
  from all VIIRS (and, as a check, Aqua) detections in that state's cells, computed with
  kill_test.weekday_index (complete years, exposure-corrected, year bootstrap, random-weekday null).
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

NE_STATES = ["Arunachal Pradesh", "Assam", "Manipur", "Meghalaya", "Mizoram", "Nagaland", "Tripura"]
LABEL = "REAL FIRMS DATA, VIIRS S-NPP 2013-2024"


def polygons(feature):
    g = feature["geometry"]
    polys = [g["coordinates"]] if g["type"] == "Polygon" else g["coordinates"]
    return [[np.asarray(ring) for ring in poly] for poly in polys]


def contains(polys, lon, lat):
    for poly in polys:
        if MplPath(poly[0]).contains_point((lon, lat)) and not any(
                MplPath(h).contains_point((lon, lat)) for h in poly[1:]):
            return True
    return False


def main():
    data_dir, cells_csv, admin1, out = sys.argv[1:5]
    os.makedirs(out, exist_ok=True)
    gj = json.load(open(admin1, encoding="utf-8"))
    india = {f["properties"]["name"]: polygons(f) for f in gj["features"] if f["properties"].get("adm0_a3") == "IND"}
    near = {f["properties"]["name"] + " (" + f["properties"]["admin"] + ")": polygons(f) for f in gj["features"]
            if f["properties"].get("adm0_a3") in ("BGD", "BTN", "MMR", "CHN", "NPL")}

    cells = pd.read_csv(cells_csv)
    ne = cells[(cells.country == "India") & (cells.cell_lon >= 89)].copy()
    aqua = ne[ne.stream == "Aqua"].set_index(["cell_lat", "cell_lon"])
    ne = ne[ne.stream == "VIIRS"].copy()

    def assign(r):
        lon, lat = r.cell_lon + 0.5, r.cell_lat + 0.5
        for name, polys in india.items():
            if contains(polys, lon, lat):
                return name
        for name, polys in near.items():
            if contains(polys, lon, lat):
                return "unassigned: centroid in " + name
        return "unassigned: centroid outside admin-1 polygons"
    ne["state"] = ne.apply(assign, axis=1)
    ne["aqua_rest_index"] = [aqua.rest_index.get((a, b), np.nan) for a, b in zip(ne.cell_lat, ne.cell_lon)]
    ne["aqua_significant"] = [aqua.significant.get((a, b), np.nan) for a, b in zip(ne.cell_lat, ne.cell_lon)]
    ne[["cell_lat", "cell_lon", "state", "rest_index", "ci_lo", "ci_hi", "q_bh", "significant",
        "mean_detections_per_year", "aqua_rest_index", "aqua_significant"]].assign(label=LABEL) \
        .to_csv(os.path.join(out, "ne_india_cells_by_state.csv"), index=False)

    # detections in the northeast cells, same cleaning and local time as kill_test.py
    veg, _ = kt.clean(rm.load(data_dir, ["India"]))
    veg = veg[veg.stream.isin(["VIIRS", "Aqua"])]
    veg = veg[(veg.longitude >= 89)]
    veg = kt.add_local_time(veg, "vegetation")
    veg["cell_lat"] = np.floor(veg.latitude).astype(int)
    veg["cell_lon"] = np.floor(veg.longitude).astype(int)
    state_of = {(a, b): s for a, b, s in zip(ne.cell_lat, ne.cell_lon, ne.state)}
    veg["state"] = [state_of.get(k) for k in zip(veg.cell_lat, veg.cell_lon)]
    sun = kt.DAYS.index("Sun")

    rows = []
    groups = [(s, ne[ne.state == s]) for s in NE_STATES] + \
             [(s, ne[ne.state == s]) for s in sorted(set(ne.state) - set(NE_STATES))]
    for state, sc in groups:
        row = {"state": state, "cells": len(sc), "cells_bh_significant": int(sc.significant.sum()),
               "median_cell_sunday_index": round(float(sc.rest_index.median()), 3) if len(sc) else np.nan}
        for stream in ["VIIRS", "Aqua"]:
            sub = veg[(veg.state == state) & (veg.stream == stream)]
            res = kt.weekday_index(sub, sun) if len(sub) else None
            tag = stream.lower()
            row[f"{tag}_detections"] = int(len(sub))
            if res is None:
                row[f"{tag}_status"] = "insufficient_data"
                continue
            lo, hi = np.percentile(res["boots"][:, sun], [2.5, 97.5])
            row.update({f"{tag}_status": "ok", f"{tag}_years": res["years"],
                        f"{tag}_sunday_index": round(float(res["mean"][sun]), 3),
                        f"{tag}_ci95": f"{lo:.3f}-{hi:.3f}", f"{tag}_p_null": round(res["p_null"], 4),
                        f"{tag}_lowest_day": kt.DAYS[int(res["mean"].argmin())]})
            if stream == "VIIRS":
                row.update({f"viirs_{d}": round(float(v), 3) for d, v in zip(kt.DAYS, res["mean"])})
        rows.append(row)
    table = pd.DataFrame(rows)
    table.insert(0, "label", LABEL + " (EXPLORATORY)")
    table.to_csv(os.path.join(out, "ne_india_states.csv"), index=False)
    pd.set_option("display.width", 220)
    print(table.drop(columns=["label"] + [f"viirs_{d}" for d in kt.DAYS]).to_string(index=False))
    plot(ne, india, near, out)


def plot(ne, india, near, out):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.colors import TwoSlopeNorm
    from matplotlib.patches import Polygon, Rectangle

    fig, ax = plt.subplots(figsize=(9.5, 8))
    xmin, xmax = ne.cell_lon.min() - 1, ne.cell_lon.max() + 2
    ymin, ymax = ne.cell_lat.min() - 1, ne.cell_lat.max() + 2
    for name, polys in {**near, **india}.items():
        for poly in polys:
            ring = poly[0]
            if not ((ring[:, 0].max() > xmin) and (ring[:, 0].min() < xmax) and
                    (ring[:, 1].max() > ymin) and (ring[:, 1].min() < ymax)):
                continue
            is_ne = name in NE_STATES
            ax.add_patch(Polygon(ring, closed=True, facecolor="#f1f3f5" if name in india else "#ffffff",
                                 edgecolor="#495057" if is_ne else "#adb5bd", linewidth=1.0 if is_ne else 0.5,
                                 zorder=1))
    norm = TwoSlopeNorm(vmin=0.4, vcenter=1, vmax=1.6)
    cmap = plt.get_cmap("RdBu_r")
    for r in ne.itertuples():
        ax.add_patch(Rectangle((r.cell_lon, r.cell_lat), 1, 1, facecolor=cmap(norm(min(max(r.rest_index, 0.4), 1.6))),
                               edgecolor="black" if r.significant else "none", linewidth=1.6 if r.significant else 0,
                               alpha=0.85, zorder=2))
    for name in NE_STATES:
        polys = india.get(name)
        if not polys:
            continue
        big = max((p[0] for p in polys), key=len)
        ax.text(big[:, 0].mean(), big[:, 1].mean(), name, fontsize=8, ha="center", va="center", zorder=3,
                bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none", alpha=0.75))
    sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
    cb = fig.colorbar(sm, ax=ax, shrink=0.75, extend="both")
    cb.set_label("Sunday index (1.0 = average day; blue = fewer Sunday detections)")
    ax.set_xlim(xmin, xmax)
    ax.set_ylim(ymin, ymax)
    ax.set_aspect(1 / np.cos(np.radians(ne.cell_lat.mean() + 0.5)))
    ax.set_xlabel("longitude")
    ax.set_ylabel("latitude")
    n_sig = int(ne.significant.sum())
    ax.set_title(f"[{LABEL}]  EXPLORATORY\nNortheast India, 1-degree VIIRS cells by state: {len(ne)} cells, "
                 f"{n_sig} significant after Benjamini-Hochberg (black outline)", fontsize=10)
    fig.text(0.01, 0.01, "State boundaries: Natural Earth admin-1 (public domain). Cells assigned to states by centroid.",
             fontsize=7, color="#495057")
    fig.tight_layout()
    fig.savefig(os.path.join(out, "ne_india_states.png"), dpi=130)
    print("figure:", os.path.join(out, "ne_india_states.png"))


if __name__ == "__main__":
    main()
