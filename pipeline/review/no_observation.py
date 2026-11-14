"""Mark satellite outages as "no observation" in the published calendar data (review E5).

python -m pipeline.review.no_observation [--check-only]

For every published national series (web/public/data/{country}.json) and daily cell file (web/public/data/cells/):
a day is marked "no observation" when the stream that supplies that day's calendar value (observed Aqua before 2013,
converted VIIRS from 2013) was in a documented outage, or had zero detections in all seven countries on that day
(treated as no data: zero burning everywhere from Australia to Brazil on the same day is not plausible). Marked days
get raw/harmonized/lo/hi = null, source "no observation" and the reason in `coverage`. The weekly climatology, anomaly
flags and critical periods are then recomputed with the unchanged pipeline.calendar.seasonal_tables, which already
excludes incomplete weeks. Before writing, the script checks that seasonal_tables reproduces the published tables from
the unmarked series. Observed per-stream counts (raw_terra/raw_aqua/raw_viirs) are left as recorded.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from pipeline import calendar
from pipeline.streaming.estimate_dictionary import compact_table, decode_table

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "web/public/data"
COUNTRIES = ["Australia", "Bangladesh", "Brazil", "Egypt", "India", "Nepal", "United_States"]
OUTAGES = [  # stream, first day, last day, reason (dates from NASA/NOAA notices; reports/review/OUTAGES.md)
    ("VIIRS", "2022-07-26", "2022-08-10", "Suomi-NPP safe mode (VIIRS returned to operation 10 Aug 2022)"),
    ("VIIRS", "2024-07-09", "2024-07-16", "Suomi-NPP GPS/geolocation anomaly"),
    ("VIIRS", "2024-07-24", "2024-08-01", "Suomi-NPP VIIRS processing outage"),
    ("Aqua", "2020-08-16", "2020-09-02", "Aqua MODIS science data outage"),
    ("Aqua", "2022-03-31", "2022-04-16", "Aqua safe mode"),
]
NO_DATA = "no detections in any of the seven countries (treated as no data)"


def load(path):
    payload = json.loads(path.read_text(encoding="utf-8"))
    table = payload["daily_compact"] if "daily_compact" in payload else payload
    return payload, table["columns"], decode_table(table)


def masks(national):
    """{stream: {date: reason}} from documented outages plus all-country zero days of that stream."""
    out = {"VIIRS": {}, "Aqua": {}}
    for stream, a, b, reason in OUTAGES:
        for d in pd.date_range(a, b).strftime("%Y-%m-%d"):
            out[stream][d] = f"no observation: {reason}"
    for stream, col, years in [("Aqua", "raw_aqua", (2003, 2012)), ("VIIRS", "raw_viirs", (2013, 2024))]:
        frame = pd.DataFrame({c: national[c].set_index("date")[col] for c in COUNTRIES})
        frame = frame[(frame.index >= f"{years[0]}-01-01") & (frame.index <= f"{years[1]}-12-31")]
        zero = frame[(frame.fillna(0) == 0).all(axis=1)].index
        for d in zero:
            out[stream].setdefault(d, f"no observation: {NO_DATA}")
    return out


def apply(columns, rows, mask):
    i = {c: k for k, c in enumerate(columns)}
    n = 0
    for row in rows:
        stream = "VIIRS" if row[i["source"]] == "converted VIIRS" else "Aqua" if row[i["source"]] == "observed Aqua" else None
        reason = mask.get(stream, {}).get(row[i["date"]]) if stream else None
        if reason:
            for c in ("raw", "harmonized", "lo", "hi"):
                row[i[c]] = None
            row[i["source"]] = "no observation"
            row[i["coverage"]] = reason
            n += 1
    return n


def tables(columns, rows):
    df = pd.DataFrame(rows, columns=columns)
    df = df[df.cell_id == "ALL"] if "cell_id" in df else df
    return calendar.seasonal_tables(df[["date", "harmonized"]])


def same(a, b, tol=1e-4):
    """Equal up to the 5-decimal rounding of published daily values (identical keys, flags and weeks)."""
    a, b = calendar.json_safe(a), calendar.json_safe(b)
    if isinstance(a, dict) and isinstance(b, dict):
        # z-scores divide by a sometimes tiny standard deviation, which amplifies the 5-decimal input rounding
        return a.keys() == b.keys() and all(same(a[k], b[k], 0.5 if k == "z_score" else tol) for k in a)
    if isinstance(a, list) and isinstance(b, list):
        return len(a) == len(b) and all(same(x, y, tol) for x, y in zip(a, b))
    if isinstance(a, (int, float)) and isinstance(b, (int, float)) and not isinstance(a, bool):
        return abs(a - b) <= tol * max(1.0, abs(b))
    return a == b


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check-only", action="store_true")
    args = ap.parse_args()
    national, loaded = {}, {}
    for c in COUNTRIES:
        payload, columns, rows = load(DATA / f"{c}.json")
        loaded[c] = (payload, columns, rows)
        df = pd.DataFrame(rows, columns=columns)
        national[c] = df[df.cell_id == "ALL"]
    mask = masks(national)
    summary = {"documented_outages": [list(o) for o in OUTAGES],
               "no_data_days": {s: sorted(d for d, r in m.items() if NO_DATA in r) for s, m in mask.items()}}
    for c in COUNTRIES:
        payload, columns, rows = loaded[c]
        clim, anomalies, critical = tables(columns, rows)
        if not (same(clim, payload["weekly_climatology"]) and same(anomalies, payload["anomalies"])
                and same(critical, payload["critical_periods"])):
            raise SystemExit(f"{c}: seasonal_tables does not reproduce the published tables; not modifying anything")
        if any(r[columns.index("source")] == "no observation" for r in rows):
            raise SystemExit(f"{c}: already marked; run on unmarked data only")
        marked = apply(columns, rows, mask)
        clim2, anomalies2, critical2 = tables(columns, rows)
        removed = len(anomalies) - len(anomalies2)
        low_before = sum(a["status"] == "low" for a in anomalies)
        low_after = sum(a["status"] == "low" for a in anomalies2)
        summary[c] = {"days_marked": marked, "anomaly_flags_before": len(anomalies), "anomaly_flags_after": len(anomalies2),
                      "low_flags_before": low_before, "low_flags_after": low_after,
                      "critical_periods_changed": not same(critical, critical2)}
        if args.check_only:
            continue
        payload["daily_compact"] = compact_table(columns, rows)
        payload["weekly_climatology"], payload["anomalies"], payload["critical_periods"] = clim2, anomalies2, critical2
        payload["meta"]["no_observation_days"] = marked
        payload["meta"]["no_observation_note"] = ("Days in a documented satellite outage, or with no detections in any of "
                                                  "the seven countries, are shown as no observation and excluded from "
                                                  "seasonal statistics and anomaly flags.")
        calendar.write_json(DATA / f"{c}.json", payload)
    cells = 0
    for path in sorted((DATA / "cells").glob("*.json")):
        table = json.loads(path.read_text(encoding="utf-8"))
        columns, rows = table["columns"], decode_table(table)
        if any(r[columns.index("source")] == "no observation" for r in rows):
            continue
        cells += apply(columns, rows, mask)
        if not args.check_only:
            calendar.write_json(path, compact_table(columns, rows))
    summary["cell_days_marked"] = cells
    out = ROOT / "reports/review/no_observation_summary.json"
    if not args.check_only:
        calendar.write_json(out, summary)
    print(json.dumps({k: v for k, v in summary.items() if k != "no_data_days"}, indent=1))
    print("no-data days:", {s: len(v) for s, v in summary["no_data_days"].items()})


if __name__ == "__main__":
    main()
