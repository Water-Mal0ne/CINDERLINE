"""Monthly Aqua-reference-equivalent series for every 0.25-degree cell (area-of-interest feature).

Frozen model, no refitting: the saved per-country selection and ratios in reports/harmonization_model.json are applied
to cell counts exactly as the national series applies them (observed Aqua 2003-2012, converted S-NPP VIIRS 2013-2024).

  python -m pipeline.area_cells count ARCHIVE_DIR [ARCHIVE_DIR ...] --out work/area_counts [--workers 20]
  python -m pipeline.area_cells build --counts work/area_counts --out web/public/data/area

count: every FIRMS country archive under ARCHIVE_DIR/{modis,viirs-snpp}/{year}/ is cleaned with pipeline.clean.clean_frame
       (official confidence filter, IANA civil time from exact coordinates, 0.25-degree cell ids), vegetation (type 0)
       only, and reduced to counts by stream x cell x local date x stratum. One Parquet file per archive.
build: per country, Aqua counts give 2003-2012 and VIIRS counts converted with the frozen selected model give
       2013-2024; daily cell values are summed to months. Months the published national series marks as
       "no observation" are listed once per country and are not cell values. Before writing, the sum over all cells is
       reconciled with the published national monthly series (web/public/data/{country}.json); the report is written to
       reports/review/area/RECONCILIATION.md.

Output per country (web/public/data/area/{country}.json, lazy-loaded): cell centres (south-west corner + 0.125),
and sparse monthly values in tenths of a detection: for each cell, alternating [month-delta, value*10] integers
where month index 0 = January 2003.
"""
from __future__ import annotations

import argparse
import json
import sys
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
COUNTRIES = ["Australia", "Bangladesh", "Brazil", "Egypt", "India", "Nepal", "United_States"]
FIRST_YEAR, SWITCH_YEAR, LAST_YEAR = 2003, 2013, 2024
MONTHS = (LAST_YEAR - FIRST_YEAR + 1) * 12
LABEL = "REAL FIRMS DATA - AREA CELLS (national calibration; local accuracy not validated)"


def _count_one(path: str) -> str | None:
    sys.path.insert(0, str(ROOT))
    from pipeline.clean import clean_frame
    from pipeline.harmonize import _strata
    p = Path(path)
    sensor, year, country = p.stem.split("_", 2)
    out = Path(_count_one.out) / f"{p.stem}.parquet"  # type: ignore[attr-defined]
    if out.exists() and out.stat().st_mtime >= p.stat().st_mtime:
        return None
    cols = ["latitude", "longitude", "acq_date", "acq_time", "satellite", "instrument", "confidence", "frp", "daynight", "type"]
    frame = pd.read_csv(p, usecols=lambda c: c in cols, low_memory=False)
    clean = clean_frame(frame, country)
    clean = clean[(clean.type == 0) & clean.stream.isin(["Aqua", "VIIRS"])]
    clean = clean.assign(stratum=_strata(clean), date=clean.local_date.dt.strftime("%Y-%m-%d"))
    counts = clean.groupby(["stream", "cell_id", "date", "stratum"], observed=True).size().rename("n").reset_index()
    counts["country"], counts["file_year"] = country, int(year)
    out.parent.mkdir(parents=True, exist_ok=True)
    counts.to_parquet(out, index=False)
    return f"{p.name}: {len(clean):,} vegetation detections, {len(counts):,} count rows"


def _init(out):
    _count_one.out = out  # type: ignore[attr-defined]


def count(archive_dirs, out, workers, smallest_first=False):
    # Only the archives the series needs: MODIS (Aqua) through the switch year, whose file also carries 31 December of
    # the previous local year in the western hemisphere; S-NPP VIIRS from the switch year onward (plus the next file's
    # local-date spill).
    def wanted(f):
        sensor, year, country = f.stem.split("_", 2)
        if country not in COUNTRIES or not year.isdigit():
            return False
        y = int(year)
        return (FIRST_YEAR - 1 <= y <= SWITCH_YEAR) if sensor == "modis" else (SWITCH_YEAR <= y <= LAST_YEAR + 1)
    files = sorted({str(f) for d in archive_dirs for sub in ("modis", "viirs-snpp") for f in Path(d, sub).glob("*/*.csv") if wanted(f)})
    # largest first so the long files start early
    files.sort(key=lambda f: Path(f).stat().st_size * (1 if smallest_first else -1))
    print(f"{len(files)} archives, {workers} workers", flush=True)
    with ProcessPoolExecutor(workers, initializer=_init, initargs=(str(out),)) as pool:
        for future in as_completed([pool.submit(_count_one, f) for f in files]):
            message = future.result()
            if message:
                print(message, flush=True)


def _published_monthly(country):
    sys.path.insert(0, str(ROOT))
    from pipeline.streaming.estimate_dictionary import decode_table
    payload = json.loads((ROOT / "web/public/data" / f"{country}.json").read_text(encoding="utf-8"))
    table = payload["daily_compact"] if "daily_compact" in payload else payload["daily"]
    rows = decode_table(table) if isinstance(table, dict) else table
    cols = table["columns"] if isinstance(table, dict) else list(rows[0].keys())
    daily = pd.DataFrame(rows, columns=cols) if isinstance(table, dict) else pd.DataFrame(rows)
    daily = daily[daily.cell_id == "ALL"]
    daily["month"] = daily.date.str.slice(0, 7)
    outage = sorted(daily.loc[daily.source == "no observation", "month"].unique())
    monthly = daily.groupby("month").harmonized.sum(min_count=1)
    return monthly, outage, payload.get("meta", {})


def build(counts_dir, out):
    model = json.loads((ROOT / "reports/harmonization_model.json").read_text(encoding="utf-8"))
    from pipeline.harmonize import predict_counts
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    report_rows, sizes = [], {}
    for country in COUNTRIES:
        files = sorted(Path(counts_dir).glob(f"*_{country}.parquet"))
        if not files:
            print(f"{country}: no counts", flush=True)
            continue
        c = pd.concat([pd.read_parquet(f) for f in files], ignore_index=True)
        c = c[c.date.str.slice(0, 4).astype(int).between(FIRST_YEAR, LAST_YEAR)]
        year = c.date.str.slice(0, 4).astype(int)
        aqua = c[(c.stream == "Aqua") & (year < SWITCH_YEAR)].copy()
        aqua["value"] = aqua.n.astype(float)
        viirs = c[(c.stream == "VIIRS") & (year >= SWITCH_YEAR)].copy()
        sel = model["selection"][country]["selected"]
        viirs["value"] = predict_counts(viirs.assign(country=country), sel, model["ratios"])
        both = pd.concat([aqua, viirs], ignore_index=True)
        both["month"] = both.date.str.slice(0, 7)
        cell_month = both.groupby(["cell_id", "month"]).value.sum()
        published, outage, meta = _published_monthly(country)
        outage_set = set(outage)
        national = cell_month.groupby(level="month").sum()
        cmp = pd.DataFrame({"cells": national, "published": published}).dropna(subset=["published"])
        cmp = cmp[~cmp.index.isin(outage_set)]
        diff = (cmp.cells - cmp.published)
        rel = diff.abs() / cmp.published.where(cmp.published > 0)
        worst = rel.idxmax() if rel.notna().any() else None
        report_rows.append({"country": country, "model": sel, "months_compared": len(cmp),
                            "max_abs_diff": float(diff.abs().max()), "max_rel_diff": float(rel.max()),
                            "worst_month": worst, "months_rel_diff_over_0.1pct": int((rel > 0.001).sum()),
                            "total_rel_diff": float(diff.sum() / cmp.published.sum())})
        # encode
        cells = sorted(cell_month.index.get_level_values(0).unique())
        month_index = {f"{y}-{m:02d}": (y - FIRST_YEAR) * 12 + m - 1 for y in range(FIRST_YEAR, LAST_YEAR + 1) for m in range(1, 13)}
        series, lat, lon = [], [], []
        grouped = cell_month.groupby(level=0)
        for cell in cells:
            s = grouped.get_group(cell).droplevel(0)
            idx = sorted((month_index[m], v) for m, v in s.items() if m in month_index and m not in outage_set)
            enc, last = [], 0
            for i, v in idx:
                tenths = int(round(v * 10))
                if tenths <= 0:
                    continue
                enc += [i - last, tenths]
                last = i
            if not enc:
                continue
            a, b = (float(x) for x in cell.split(":"))
            series.append(enc)
            lat.append(round(a + 0.125, 3))
            lon.append(round(b + 0.125, 3))
        payload = {"label": LABEL, "country": country, "model": sel, "reference": meta.get("reference", "MODIS Aqua"),
                   "first_month": f"{FIRST_YEAR}-01", "months": MONTHS, "grid": 0.25, "unit": "tenths of Aqua-reference-equivalent detections",
                   "switch": f"{SWITCH_YEAR}-01", "outage_months": outage,
                   "note": "Area values use national calibration; local accuracy has not been validated.",
                   "lat": lat, "lon": lon, "series": series}
        path = out / f"{country}.json"
        path.write_text(json.dumps(payload, separators=(",", ":")), encoding="utf-8")
        sizes[country] = path.stat().st_size
        print(f"{country}: {len(series):,} cells, {path.stat().st_size / 2**20:.2f} MiB, reconciliation max rel {report_rows[-1]['max_rel_diff']:.2e}", flush=True)
    rep = pd.DataFrame(report_rows)
    review = ROOT / "reports/review/area"
    review.mkdir(parents=True, exist_ok=True)
    rep.insert(0, "label", LABEL)
    rep.to_csv(review / "reconciliation.csv", index=False)
    (review / "sizes.json").write_text(json.dumps({k: v for k, v in sizes.items()}, indent=1), encoding="utf-8")
    print(rep.drop(columns=["label"]).to_string(index=False))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("count")
    a.add_argument("archives", nargs="+")
    a.add_argument("--out", default="work/area_counts")
    a.add_argument("--workers", type=int, default=20)
    a.add_argument("--smallest-first", action="store_true", help="order for a second process sharing the work")
    b = sub.add_parser("build")
    b.add_argument("--counts", default="work/area_counts")
    b.add_argument("--out", default="web/public/data/area")
    args = ap.parse_args()
    if args.cmd == "count":
        count(args.archives, ROOT / args.out if not Path(args.out).is_absolute() else Path(args.out), args.workers, args.smallest_first)
    else:
        build(ROOT / args.counts if not Path(args.counts).is_absolute() else Path(args.counts), ROOT / args.out)


if __name__ == "__main__":
    main()
