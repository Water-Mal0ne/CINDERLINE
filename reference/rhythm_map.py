"""
FIRETRACE rhythm map (EXPLORATORY): where inside a country is the rest-day dip?

Run after download.py:  python rhythm_map.py [data_dir] [--label "REAL FIRMS DATA, VIIRS S-NPP 2013-2024"]
Needs: pandas, numpy, matplotlib, timezonefinder. Reuses kill_test.py (imported, not modified).

Same per-row method as kill_test.py: vegetation fires only, low confidence dropped, UTC converted
to local civil time, complete calendar years only, exposure-corrected weekday index per year,
95% CI by bootstrapping whole years, null test = rest day vs a random weekday each year.

Differences, all specific to the per-cell question:
- Unit is a 1 x 1 degree grid cell (south-west corner = floor(lat), floor(lon)), per country file.
  A cell on a border can appear once per country.
- Cell kept if it averages >= 300 detections per complete study year AND has >= 8 usable years.
  A usable year is a complete year with >= 140 detections in that cell (kill_test.py's per-year
  minimum), so a single year's weekday rates are not built from a handful of detections.
- 20000 null draws instead of 5000: same test, finer p-values. With 5000 draws the smallest
  possible p is 0.0002, which is too coarse for a false-discovery correction over many cells.
- Benjamini-Hochberg at 5% across all cells of one stream (all countries pooled). A cell is
  "significant" when its BH-adjusted q < 0.05. rest_is_lowest is reported separately.
- VIIRS is the map; Aqua is computed the same way as a check.

Outputs: rhythm_cells.csv, rhythm_cells.geojson (VIIRS cells, Aqua check fields attached),
         rhythm_map_<Country>.png
"""
import argparse
import datetime as dt
import glob
import json
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kill_test as kt  # noqa: E402

DAYS = kt.DAYS
DEFAULT_COUNTRIES = ["United_States", "Brazil", "Australia", "India"]
STREAMS = ["VIIRS", "Aqua"]
MAP_STREAM, CHECK_STREAM = "VIIRS", "Aqua"
N_BOOT, N_NULL = 2000, 20000
FDR_Q = 0.05
rng = np.random.default_rng(42)


def load(data_dir, countries):
    """kill_test.load, restricted to the countries we need (saves memory and time)."""
    frames = []
    for path in sorted(glob.glob(os.path.join(data_dir, "**", "*.csv"), recursive=True)):
        parts = os.path.basename(path)[:-4].split("_", 2)
        if len(parts) < 3 or parts[2] not in countries:
            continue
        df = pd.read_csv(path, low_memory=False, usecols=lambda c: c in kt.USE_COLS)
        df["country"] = parts[2]
        df["file_year"] = int(parts[1])
        for c in kt.CAT_COLS:
            if c in df:
                df[c] = df[c].astype(str).astype("category")
        frames.append(df)
    if not frames:
        sys.exit(f"No FIRMS CSV files for {countries} under {data_dir}/")
    for c in kt.CAT_COLS:
        cats = sorted(set().union(*(f[c].cat.categories for f in frames if c in f)))
        for f in frames:
            if c in f:
                f[c] = f[c].cat.set_categories(cats)
    kt.diag["files"] = len(frames)
    df = pd.concat(frames, ignore_index=True)
    del frames
    kt.diag["rows_loaded"] = int(len(df))
    return df


def bh(p, q=FDR_Q):
    """Benjamini-Hochberg. Returns (significant mask, adjusted q-values)."""
    p = np.asarray(p, float)
    m = len(p)
    if m == 0:
        return np.zeros(0, bool), np.zeros(0)
    order = np.argsort(p)
    ranked = p[order] * m / np.arange(1, m + 1)
    adj = np.minimum.accumulate(ranked[::-1])[::-1].clip(max=1)
    qv = np.empty(m)
    qv[order] = adj
    return qv < q, qv


def cell_table(veg, min_mean, min_year, min_years):
    this_year = dt.date.today().year
    veg = veg.assign(cell_lat=np.floor(veg["latitude"]).astype("int16"),
                     cell_lon=np.floor(veg["longitude"]).astype("int16"),
                     fmatch=(veg["file_year"] == veg["year"]))
    keys = ["country", "stream", "cell_lat", "cell_lon", "year"]
    counts = veg.groupby(keys + ["weekday"], observed=True).size().unstack("weekday", fill_value=0)
    counts = counts.reindex(columns=range(7), fill_value=0)
    fm = veg.groupby(keys, observed=True)["fmatch"].mean()
    counts = counts.join(fm)
    # study years: complete calendar years present in the file names
    fy = sorted(int(y) for y in veg["file_year"].unique() if int(y) < this_year)
    n_study = len(fy)
    kt.diag["study_years"] = f"{fy[0]}-{fy[-1]} ({n_study})"
    exposure = {y: kt.weekday_exposure(y) for y in fy}
    footprint = veg.groupby(["country", "stream", "cell_lat", "cell_lon"], observed=True).size()

    rows = []
    for (country, stream, la, lo), grp in counts.groupby(level=[0, 1, 2, 3], observed=True):
        yrs = grp.index.get_level_values("year").astype(int)
        complete = (yrs < this_year) & (grp["fmatch"].values >= 0.95) & np.isin(yrs, fy)
        c = grp[list(range(7))].values[complete]
        y_ok = yrs[complete]
        total = c.sum()
        mean_per_year = total / n_study
        n_year = c.sum(axis=1)
        use = n_year >= min_year
        if mean_per_year < min_mean or use.sum() < min_years:
            continue
        Y = np.array([(r / exposure[y]) for r, y in zip(c[use], y_ok[use])])
        Y = Y / Y.mean(axis=1, keepdims=True)
        n = len(Y)
        r = DAYS.index(kt.COUNTRIES[country]["rest"])
        boots = Y[rng.integers(0, n, (N_BOOT, n))].mean(axis=1)
        null = Y[np.arange(n)[None, :].repeat(N_NULL, 0), rng.integers(0, 7, (N_NULL, n))].mean(axis=1)
        mean = Y.mean(axis=0)
        lo95, hi95 = np.percentile(boots[:, r], [2.5, 97.5])
        rows.append({
            "country": country, "stream": stream, "cell_lat": int(la), "cell_lon": int(lo),
            "rest_day": DAYS[r], "years": n, "mean_detections_per_year": round(float(mean_per_year), 1),
            "rest_index": round(float(mean[r]), 3), "ci_lo": round(float(lo95), 3),
            "ci_hi": round(float(hi95), 3),
            "p_null": float((np.sum(null <= mean[r]) + 1) / (N_NULL + 1)),
            "lowest_day": DAYS[int(mean.argmin())], "rest_is_lowest": bool(mean[r] == mean.min()),
            **{d: round(float(v), 3) for d, v in zip(DAYS, mean)},
        })
    out = pd.DataFrame(rows)
    out["q_bh"], out["significant"] = np.nan, False
    for stream in STREAMS:
        m = out["stream"] == stream
        if m.any():
            sig, qv = bh(out.loc[m, "p_null"].values)
            out.loc[m, "q_bh"] = qv.round(5)
            out.loc[m, "significant"] = sig
    return out, footprint


def aqua_check(cells):
    v = cells[cells.stream == MAP_STREAM]
    a = cells[cells.stream == CHECK_STREAM]
    both = v.merge(a, on=["country", "cell_lat", "cell_lon"], suffixes=("_v", "_a"))
    res = {}
    for country in ["ALL"] + sorted(cells.country.unique()):
        b = both if country == "ALL" else both[both.country == country]
        vs = b[b.significant_v]
        res[country] = {
            "cells_with_both": int(len(b)),
            "corr_rest_index": round(float(np.corrcoef(b.rest_index_v, b.rest_index_a)[0, 1]), 3)
            if len(b) > 2 else None,
            "share_same_side_of_1": round(float(((b.rest_index_v < 1) == (b.rest_index_a < 1)).mean()), 3)
            if len(b) else None,
            "viirs_sig_cells_with_aqua": int(len(vs)),
            "of_those_aqua_below_1": int((vs.rest_index_a < 1).sum()),
            "of_those_aqua_significant": int(vs.significant_a.sum()),
        }
    return res, both


def write_geojson(cells, path, label):
    v = cells[cells.stream == MAP_STREAM]
    a = cells[cells.stream == CHECK_STREAM].set_index(["country", "cell_lat", "cell_lon"])
    feats = []
    for _, r in v.iterrows():
        la, lo = int(r.cell_lat), int(r.cell_lon)
        props = {k: (v_.item() if hasattr(v_, "item") else v_) for k, v_ in r.items() if k != "stream"}
        key = (r.country, la, lo)
        if key in a.index:
            ar = a.loc[key]
            props.update(aqua_rest_index=float(ar.rest_index), aqua_ci_lo=float(ar.ci_lo),
                         aqua_ci_hi=float(ar.ci_hi), aqua_q_bh=float(ar.q_bh),
                         aqua_significant=bool(ar.significant))
        else:
            props.update(aqua_rest_index=None, aqua_ci_lo=None, aqua_ci_hi=None,
                         aqua_q_bh=None, aqua_significant=None)
        feats.append({"type": "Feature", "properties": props, "geometry": {
            "type": "Polygon",
            "coordinates": [[[lo, la], [lo + 1, la], [lo + 1, la + 1], [lo, la + 1], [lo, la]]]}})
    gj = {"type": "FeatureCollection",
          "metadata": {"label": label, "stream": MAP_STREAM, "exploratory": True,
                       "index_meaning": "rest-day detections / average-day detections; 1.0 = average",
                       "significant": f"Benjamini-Hochberg q < {FDR_Q} across all {MAP_STREAM} cells",
                       "cell": "1 x 1 degree, coordinates are the south-west corner"},
          "features": feats}
    with open(path, "w") as f:
        json.dump(gj, f, allow_nan=False)


def plot(cells, footprint, label, out_dir, country):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.collections import PatchCollection
    from matplotlib.colors import TwoSlopeNorm
    from matplotlib.patches import Patch, Rectangle

    c = cells[(cells.stream == MAP_STREAM) & (cells.country == country)]
    try:
        fp = footprint.loc[(country, MAP_STREAM)].index
    except KeyError:
        return None
    lats = pd.Series(np.asarray(fp.get_level_values(0), int))
    lons = pd.Series(np.asarray(fp.get_level_values(1), int))
    # wrap Aleutian cells (lon > 170 E) next to Alaska so the US map is not split
    wrap = lambda x: x - 360 if (country == "United_States" and x > 0) else x
    w = max(lons.map(wrap).max() + 1 - lons.map(wrap).min(), 5)
    h = max(lats.max() + 1 - lats.min(), 5)
    aspect = 1 / np.cos(np.radians(lats.mean()))
    fig_w = 11
    fig, ax = plt.subplots(figsize=(fig_w, min(max(fig_w * h * aspect / w, 4), 12) + 1.2))
    ax.add_collection(PatchCollection([Rectangle((wrap(lo), la), 1, 1) for la, lo in zip(lats, lons)],
                                      facecolor="#e9ecef", edgecolor="none"))
    d = 0.3
    norm = TwoSlopeNorm(vmin=1 - d, vcenter=1, vmax=1 + d)
    pc = PatchCollection([Rectangle((wrap(lo), la), 1, 1) for la, lo in zip(c.cell_lat, c.cell_lon)],
                         cmap="RdBu_r", norm=norm, edgecolor="none")
    pc.set_array(c.rest_index.clip(1 - d, 1 + d).values)
    ax.add_collection(pc)
    s = c[c.significant]
    ax.add_collection(PatchCollection([Rectangle((wrap(lo), la), 1, 1)
                                       for la, lo in zip(s.cell_lat, s.cell_lon)],
                                      facecolor="none", edgecolor="black", linewidth=1.1))
    ax.set_xlim(lons.map(wrap).min() - 1, lons.map(wrap).max() + 2)
    ax.set_ylim(lats.min() - 1, lats.max() + 2)
    ax.set_aspect(aspect)
    ax.set_xlabel("longitude")
    ax.set_ylabel("latitude")
    cb = fig.colorbar(pc, ax=ax, shrink=0.8, extend="both")
    rest = kt.COUNTRIES[country]["rest"]
    cb.set_label(f"{rest} index (1.0 = average day; blue = fewer {rest} detections)")
    n_dip_sig = int(((s.rest_index < 1)).sum())
    ax.legend(handles=[Patch(facecolor="#e9ecef", label="has detections, below cell threshold"),
                       Patch(facecolor="none", edgecolor="black", label=f"significant (BH q < {FDR_Q})")],
              loc="lower left", fontsize=8, framealpha=0.9)
    ax.set_title(f"[{label}]  EXPLORATORY\n{country}: predicted rest day {rest}, 1-degree cells. "
                 f"{len(c)} cells analysed, {len(s)} significant ({n_dip_sig} dips)", fontsize=10)
    if "SYNTHETIC" in label.upper():
        fig.text(0.5, 0.5, "SYNTHETIC DATA", fontsize=60, color="red", alpha=0.15,
                 ha="center", va="center", rotation=25)
    fig.tight_layout()
    path = os.path.join(out_dir, f"rhythm_map_{country}.png")
    fig.savefig(path, dpi=120)
    plt.close(fig)
    return path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("data_dir", nargs="?", default="data")
    ap.add_argument("--label", default="REAL FIRMS DATA, VIIRS S-NPP 2013-2024")
    ap.add_argument("--countries", nargs="+", default=DEFAULT_COUNTRIES)
    ap.add_argument("--out", default=".")
    # thresholds: defaults are the agreed ones; only lower them for synthetic tests
    ap.add_argument("--min-mean", type=float, default=300)
    ap.add_argument("--min-year", type=int, default=kt.MIN_DETECTIONS_PER_YEAR)
    ap.add_argument("--min-years", type=int, default=8)
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    kt.diag.clear()
    kt.diag["label"] = a.label

    veg, static = kt.clean(load(a.data_dir, a.countries))
    del static
    veg = veg[veg["stream"].isin(STREAMS)]
    veg = kt.add_local_time(veg, "vegetation")
    cells, footprint = cell_table(veg, a.min_mean, a.min_year, a.min_years)
    del veg
    cells = cells.sort_values(["stream", "country", "cell_lat", "cell_lon"]).reset_index(drop=True)
    cells.insert(0, "label", a.label)
    cells.to_csv(os.path.join(a.out, "rhythm_cells.csv"), index=False)
    write_geojson(cells, os.path.join(a.out, "rhythm_cells.geojson"), a.label)
    check, _ = aqua_check(cells)

    summary = {"label": a.label, "thresholds": {"min_mean_per_year": a.min_mean,
               "min_detections_usable_year": a.min_year, "min_usable_years": a.min_years},
               "diagnostics": kt.diag, "per_country": {}, "aqua_check": check}
    for (country, stream), g in cells.groupby(["country", "stream"]):
        summary["per_country"].setdefault(country, {})[stream] = {
            "cells": int(len(g)), "significant": int(g.significant.sum()),
            "significant_dip_and_lowest": int((g.significant & g.rest_is_lowest).sum()),
            "cells_below_1": int((g.rest_index < 1).sum()),
            "cells_ci_above_1": int((g.ci_lo > 1).sum()),
            "median_rest_index": round(float(g.rest_index.median()), 3),
        }
    with open(os.path.join(a.out, "rhythm_summary.json"), "w") as f:
        json.dump(summary, f, indent=2, default=str)

    print(f"[{a.label}]  EXPLORATORY per-cell rest-day map")
    print(json.dumps(summary, indent=2, default=str))
    for country in a.countries:
        p = plot(cells, footprint, a.label, a.out, country)
        if p:
            print("map saved:", p)


if __name__ == "__main__":
    main()
