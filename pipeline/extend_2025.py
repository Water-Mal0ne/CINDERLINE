"""Extend the published calendar with 2025: converted S-NPP VIIRS beyond the validation period (frozen model, no refitting).

  python -m pipeline.extend_2025 count ARCHIVE_DIR [ARCHIVE_DIR ...] --out work/extend_2025 [--workers 12]
  python -m pipeline.extend_2025 build --counts work/extend_2025 [--dry-run]

count: FIRMS 2025 country archives (viirs-snpp and modis) plus the 2024 archives (whose UTC records spill into
       1 January 2025 local time) are cleaned with pipeline.clean.clean_frame (official confidence filter, IANA civil
       time from exact coordinates, 0.25-degree cells), vegetation (type 0) only, and reduced to counts by
       stream x cell x local date x stratum.
build: for every country, daily 2025 rows are produced for the national total and for each of the 12 published cells,
       in the published row format: raw Terra/Aqua/VIIRS counts, raw baseline (VIIRS), harmonized = VIIRS converted with
       the frozen selected model and ratios (reports/harmonization_model.json), source "converted VIIRS, beyond the
       validation period". The 200-draw calibration interval needs the full training bootstrap, which is not
       re-run here, so lo/hi are left empty (not zero) for 2025. Days with no S-NPP VIIRS detections in any of the
       seven countries are "no observation", as in the published 2003-2024 series. The rows are appended to the
       published national and cell files; 2003-2024 rows, weekly climatology, anomaly flags, critical periods,
       evaluation and the rhythm results are left unchanged (they remain based on 2003-2024).
       Out-of-sample continuity check: weekly (W-MON) converted VIIRS against observed MODIS Aqua for 2025, per
       country, written to reports/review/extend2025/.
No archive for 2026 exists yet, so 31 December 2025 in the western hemisphere lacks the evening hours that fall on
1 January 2026 UTC; that day's coverage says so.
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
YEAR = 2025
SOURCE = "converted VIIRS, beyond the validation period"
LABEL = "REAL FIRMS DATA - 2025 EXTENSION (frozen model, beyond the validation period)"
WESTERN = {"United_States", "Brazil"}
# Partial-day S-NPP VIIRS gap found in the 2025 archive: zero VIIRS detections in five eastern-hemisphere countries on
# this local date while MODIS Aqua and Terra recorded hundreds (Australia: Aqua 890, Terra 308, VIIRS 0; India: Aqua 122,
# VIIRS 0) and Brazil/United States VIIRS were normal. Marked as no observation for those countries only.
VIIRS_GAPS = {"2025-11-12": {"Australia", "Bangladesh", "Egypt", "India", "Nepal"}}
GAP_REASON = ("no observation: S-NPP VIIRS data gap (zero VIIRS detections in five eastern-hemisphere countries while "
              "MODIS recorded detections)")


def _count_one(path: str, out_dir: str):
    sys.path.insert(0, str(ROOT))
    from pipeline.clean import clean_frame
    from pipeline.harmonize import _strata
    p = Path(path)
    out = Path(out_dir) / f"{p.stem}.parquet"
    if out.exists() and out.stat().st_mtime >= p.stat().st_mtime:
        return None
    country = p.stem.split("_", 2)[2]
    cols = ["latitude", "longitude", "acq_date", "acq_time", "satellite", "instrument", "confidence", "frp", "daynight", "type"]
    clean = clean_frame(pd.read_csv(p, usecols=lambda c: c in cols, low_memory=False), country)
    clean = clean[(clean.type == 0) & clean.stream.isin(["Terra", "Aqua", "VIIRS"]) & (clean.year == YEAR)]
    clean = clean.assign(stratum=_strata(clean), date=clean.local_date.dt.strftime("%Y-%m-%d"))
    counts = clean.groupby(["stream", "cell_id", "date", "stratum"], observed=True).size().rename("n").reset_index()
    counts["country"] = country
    out.parent.mkdir(parents=True, exist_ok=True)
    counts.to_parquet(out, index=False)
    return f"{p.name}: {len(clean):,} vegetation detections dated {YEAR}"


def count(dirs, out, workers):
    files = [str(f) for d in dirs for sensor in ("modis", "viirs-snpp") for y in (YEAR - 1, YEAR)
             for f in Path(d, sensor, str(y)).glob(f"{sensor}_{y}_*.csv") if f.stem.split("_", 2)[2] in COUNTRIES]
    files.sort(key=lambda f: -Path(f).stat().st_size)
    print(f"{len(files)} archives", flush=True)
    with ProcessPoolExecutor(workers) as pool:
        for fut in as_completed([pool.submit(_count_one, f, str(out)) for f in files]):
            if (msg := fut.result()):
                print(msg, flush=True)


def _load(path):
    sys.path.insert(0, str(ROOT))
    from pipeline.streaming.estimate_dictionary import decode_table
    payload = json.loads(path.read_text(encoding="utf-8"))
    table = payload["daily_compact"] if "daily_compact" in payload else payload
    return payload, table["columns"], decode_table(table)


def build(counts_dir, dry_run=False):
    from pipeline import calendar
    from pipeline.harmonize import metrics, predict_counts
    from pipeline.streaming.estimate_dictionary import compact_table
    model = json.loads((ROOT / "reports/harmonization_model.json").read_text(encoding="utf-8"))
    counts = pd.concat([pd.read_parquet(f) for f in Path(counts_dir).glob("*.parquet")], ignore_index=True)
    counts = counts[counts.date.str.startswith(str(YEAR))]
    dates = pd.date_range(f"{YEAR}-01-01", f"{YEAR}-12-31").strftime("%Y-%m-%d")
    viirs_all = counts[counts.stream == "VIIRS"].groupby(["country", "date"]).n.sum().unstack("country").reindex(dates).fillna(0)
    missing = [c for c in COUNTRIES if c not in viirs_all]
    if missing:
        raise SystemExit(f"No 2025 VIIRS counts for {missing}")
    no_data = set(viirs_all.index[(viirs_all[COUNTRIES] == 0).all(axis=1)])
    data = ROOT / "web/public/data"
    continuity, summary = [], {"no_observation_days_2025": sorted(no_data)}
    for country in COUNTRIES:
        sel = model["selection"][country]["selected"]
        c = counts[counts.country == country]
        payload, columns, rows = _load(data / f"{country}.json")
        if any(r[columns.index("date")].startswith(str(YEAR)) for r in rows):
            raise SystemExit(f"{country}: 2025 rows already present; run on the unextended files only")
        cell_files = {cell["id"]: cell.get("file") for cell in payload["cells"]}

        def daily(sub):
            by = {s: sub[sub.stream == s].groupby("date").n.sum().reindex(dates).fillna(0) for s in ("Terra", "Aqua", "VIIRS")}
            v = sub[sub.stream == "VIIRS"]
            conv = pd.Series(predict_counts(v.assign(country=country), sel, model["ratios"]), index=v.index).groupby(v.date).sum().reindex(dates).fillna(0) if len(v) else pd.Series(0.0, index=dates)
            return by, conv

        def make_rows(cell_id, sub):
            by, conv = daily(sub)
            out = []
            for d in dates:
                blocked = d in no_data or country in VIIRS_GAPS.get(d, set())
                cov = (f"archive: Terra,Aqua,VIIRS {YEAR}; beyond the validation period; observation coverage unknown"
                       + ("; no 2026 archive yet, so late-evening local detections on 31 December may be missing" if d == f"{YEAR}-12-31" and country in WESTERN else ""))
                row = {"date": d, "cell_id": cell_id, "raw_terra": float(by["Terra"][d]), "raw_aqua": float(by["Aqua"][d]), "raw_viirs": float(by["VIIRS"][d]),
                       "raw": None if blocked else float(by["VIIRS"][d]), "harmonized": None if blocked else round(float(conv[d]), 5),
                       "lo": None, "hi": None,
                       "coverage": (GAP_REASON if country in VIIRS_GAPS.get(d, set()) else "no observation: no S-NPP VIIRS detections in any of the seven countries (treated as no data)") if blocked else cov,
                       "source": "no observation" if blocked else SOURCE, "model": sel}
                out.append([row[k] for k in columns])
            return out, by, conv

        new_rows, by, conv = make_rows("ALL", c)
        rows_out = rows + new_rows
        # continuity check, national, weekly W-MON over 2025 (no-observation days excluded on both sides)
        frame = pd.DataFrame({"aqua": by["Aqua"], "converted": conv, "viirs": by["VIIRS"]})
        frame.index = pd.to_datetime(frame.index)
        gaps = {d for d, cs in VIIRS_GAPS.items() if country in cs}
        frame = frame[~frame.index.strftime("%Y-%m-%d").isin(no_data | gaps)]
        weekly = frame.resample("W-MON").sum()
        m = metrics(weekly.aqua, weekly.converted)
        test = pd.read_csv(ROOT / "reports/review/layer1_table.csv")
        t = test[(test.country.str.replace(" ", "_") == country) & (test.model == sel)]
        continuity.append({"country": country, "model": sel, "weeks": len(weekly), "aqua_detections": int(frame.aqua.sum()),
                           "converted_viirs": round(float(frame.converted.sum()), 1),
                           "bias_pct_2025": round(m["bias_pct"], 1), "weekly_r_2025": round(m["correlation"], 3), "weekly_mae_2025": round(m["mae"], 1),
                           "raw_viirs_per_aqua_2025": round(float(frame.viirs.sum() / frame.aqua.sum()), 2) if frame.aqua.sum() else None,
                           **({"bias_pct_test_2020_2024": round(float(t.iloc[0]["bias_pct"]), 1), "weekly_r_test_2020_2024": round(float(t.iloc[0]["correlation"]), 3)} if len(t) else {})})
        summary[country] = {"days_added": len(dates), "no_observation_days": sorted(no_data | {d for d, cs in VIIRS_GAPS.items() if country in cs})}
        if dry_run:
            continue
        # cells
        for cell_id, file in cell_files.items():
            if not file:
                continue
            path = data / file
            table = json.loads(path.read_text(encoding="utf-8"))
            from pipeline.streaming.estimate_dictionary import decode_table
            ccols, crows = table["columns"], decode_table(table)
            extra, _, _ = make_rows(cell_id, c[c.cell_id == cell_id])
            if ccols != columns:
                extra = [[dict(zip(columns, r))[k] for k in ccols] for r in extra]
            calendar.write_json(path, compact_table(ccols, crows + extra))
        payload["daily_compact"] = compact_table(columns, rows_out)
        payload["meta"]["period_end"] = f"{YEAR}-12-31"
        payload["meta"]["extension_note"] = (f"{YEAR} is converted S-NPP VIIRS beyond the validation period: the frozen {sel} model is applied "
                                             f"with no refitting. Calibration intervals are not computed for {YEAR}. Weekly climatology, anomaly flags, "
                                             "critical periods, evaluation and the weekly rhythm results remain based on 2003-2024.")
        calendar.write_json(data / f"{country}.json", payload)
    out = ROOT / "reports/review/extend2025"
    out.mkdir(parents=True, exist_ok=True)
    cont = pd.DataFrame(continuity)
    cont.insert(0, "label", LABEL)
    cont.to_csv(out / "continuity_2025.csv", index=False)
    (out / "summary.json").write_text(json.dumps(summary, indent=1), encoding="utf-8")
    pd.set_option("display.width", 220)
    print(cont.drop(columns=["label"]).to_string(index=False))
    print("no-observation days 2025:", sorted(no_data))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("count")
    a.add_argument("archives", nargs="+")
    a.add_argument("--out", default="work/extend_2025")
    a.add_argument("--workers", type=int, default=12)
    b = sub.add_parser("build")
    b.add_argument("--counts", default="work/extend_2025")
    b.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    if args.cmd == "count":
        count(args.archives, ROOT / args.out, args.workers)
    else:
        build(ROOT / args.counts, args.dry_run)


if __name__ == "__main__":
    main()
