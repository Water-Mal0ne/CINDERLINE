"""Build reproducible seasonal calendars and static application payloads."""
from __future__ import annotations

import datetime as dt
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd

CENTROIDS = {"Nepal": [84.1, 28.2], "United_States": [-98.6, 39.8],
             "Australia": [134, -25], "Bangladesh": [90.3, 23.7],
             "Egypt": [30, 27], "India": [79, 22], "Brazil": [-52, -12]}
DAY_FIELDS = ["date", "cell_id", "raw_terra", "raw_aqua", "raw_viirs", "raw",
              "harmonized", "lo", "hi", "coverage", "source", "model"]


def json_safe(value):
    if isinstance(value, dict):
        return {str(k): json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, np.ndarray)):
        return [json_safe(v) for v in value]
    if isinstance(value, (dt.date, dt.datetime, pd.Timestamp)):
        return value.isoformat()[:10] if not isinstance(value, dt.datetime) else value.isoformat()
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (float, np.floating)):
        return round(float(value), 5) if math.isfinite(value) else None
    if isinstance(value, np.bool_):
        return bool(value)
    if value is pd.NA or value is pd.NaT:
        return None
    return value


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(json_safe(value), ensure_ascii=False, allow_nan=False,
                               separators=(",", ":")), encoding="utf-8")


def normalized_daily(frame):
    frame = frame.copy()
    frame["date"] = pd.to_datetime(frame["date"])
    if "raw" not in frame:
        frame["raw"] = frame["raw_viirs"].where(frame["raw_viirs"].notna(), frame["raw_aqua"])
    frame["date"] = frame["date"].dt.strftime("%Y-%m-%d")
    for col in DAY_FIELDS:
        if col not in frame:
            frame[col] = None
    return frame.sort_values("date")[DAY_FIELDS]


def seasonal_tables(daily):
    """Jan-1 anchored seven-day bins; historical anomalies exclude their own year.

    Values are recorded activity, not estimates of zero on unobserved days.
    Calendar-day absence is retained in completeness fields; no gap filling.
    """
    if daily.empty:
        return [], [], []
    d = daily.copy()
    dates = pd.to_datetime(d.date)
    d["year"] = dates.dt.year
    d["week"] = (dates.dt.dayofyear - 1) // 7 + 1
    weekly = d.groupby(["year", "week"], as_index=False).agg(
        value=("harmonized", lambda x: x.sum(min_count=1)),
        date=("date", "min"), days_with_values=("harmonized", "count"),
        distinct_dates=("date", "nunique"))
    # Compare complete seven-day bins only. The 1–2 day year-end tail remains
    # visible in the calendar but cannot be compared to a full weekly total.
    eligible = (weekly.week <= 52) & (weekly.days_with_values == 7) & (weekly.distinct_dates == 7)
    weekly.loc[~eligible, "value"] = np.nan
    stats = []
    for week, g in weekly.groupby("week"):
        vals = g.value.dropna()
        if len(vals) < 3:
            stats.append(dict(week=int(week), median=None, p10=None, p90=None,
                              critical=False, years=int(len(vals))))
        else:
            stats.append(dict(week=int(week), median=float(vals.median()),
                              p10=float(vals.quantile(.1)), p90=float(vals.quantile(.9)),
                              critical=False, years=int(len(vals))))
    medians = [x["median"] for x in stats if x["median"] is not None]
    threshold = np.quantile(medians, .75) if medians else np.inf
    for s in stats:
        s["critical"] = bool(s["median"] is not None and s["median"] > 0
                             and s["median"] >= threshold)
    anomalies = []
    for row in weekly.itertuples():
        ref = weekly[(weekly.week == row.week) & (weekly.year != row.year)].value.dropna()
        if len(ref) < 3 or pd.isna(row.value):
            continue
        lower, upper = ref.quantile([.1, .9])
        state = "high" if row.value > upper else "low" if row.value < lower else "typical"
        if state != "typical":
            sd = ref.std(ddof=1)
            anomalies.append(dict(date=str(row.date), week=int(row.week), value=float(row.value),
                                  z_score=float((row.value - ref.mean()) / sd) if sd > 0 else None,
                                  status=state, reference_years=len(ref),
                                  days_with_values=int(row.days_with_values)))
    critical = []
    for s in stats:
        if s["critical"]:
            if critical and critical[-1]["end_week"] + 1 == s["week"]:
                critical[-1]["end_week"] = s["week"]
            else:
                critical.append(dict(start_week=s["week"], end_week=s["week"],
                                     label="Historical high-activity period"))
    return stats, anomalies, critical


def export_ics(periods, path, year):
    lines = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//FIRETRACE//Seasonal calendar//EN",
             "CALSCALE:GREGORIAN"]
    for p in periods:
        start = dt.date(year, 1, 1) + dt.timedelta(days=(p["start_week"] - 1) * 7)
        end = min(dt.date(year + 1, 1, 1),
                  dt.date(year, 1, 1) + dt.timedelta(days=p["end_week"] * 7))
        lines += ["BEGIN:VEVENT", f"UID:firetrace-{Path(path).stem}-{year}-{p['start_week']}",
                  "DTSTAMP:20261114T000000Z", f"DTSTART;VALUE=DATE:{start:%Y%m%d}",
                  f"DTEND;VALUE=DATE:{end:%Y%m%d}", "SUMMARY:Historical high fire activity",
                  "DESCRIPTION:Historical seasonal pattern. Not a forecast or safety alert.",
                  "END:VEVENT"]
    lines += ["END:VCALENDAR", ""]
    Path(path).write_text("\r\n".join(lines), encoding="utf-8", newline="")


def build(harmonized, evaluation, rhythm, output_dir, detections=None, label="REAL FIRMS DATA",
          max_cells=96):
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    regions = []
    limitations = [
        "Hotspots are detections, not independent fires or burned area.",
        "Cloud and overpass coverage are not measured. Missing observations are not zero fire activity.",
        "Historical critical periods are not forecasts. Calendar bins start January 1, not ISO weeks.",
        "The raw baseline switches instruments; it is a constructed comparison.",
    ]
    for region, r in harmonized.groupby("region"):
        agg = r[r.cell_id == "ALL"]
        if agg.empty:
            continue
        daily = normalized_daily(agg)
        clim, anomalies, periods = seasonal_tables(daily)
        cells = []
        available_cells = r[r.cell_id != "ALL"]
        rank = available_cells.groupby("cell_id").harmonized.sum(min_count=1).sort_values(ascending=False)
        selected = rank.head(max_cells).index
        coords = {}
        total_cells = len(rank)
        if detections is not None and not detections.empty:
            locs = detections[detections.country == region].groupby("cell_id")[["lat", "lon"]].mean()
            coords = locs.to_dict("index")
            total_cells = len(locs)
        for cid in selected:
            c = available_cells[available_cells.cell_id == cid]
            # Location is the geometric center of the analysis grid, not the
            # mean location of detections, which moves as observations change.
            south, west = (float(part) for part in str(cid).split(":"))
            xy = {"lat": south + .125, "lon": west + .125}
            if not xy:
                continue
            cell_daily = normalized_daily(c)
            # Grid IDs contain ':'; encode it as '_' for ordinary Windows files
            # rather than NTFS alternate data streams.
            cell_file = f"cells/{region}_{str(cid).replace(':', '_')}.json"
            write_json(out / cell_file, dict(columns=DAY_FIELDS,
                       rows=cell_daily.where(pd.notna(cell_daily), None).values.tolist()))
            cells.append(dict(id=str(cid), lat=float(xy["lat"]), lon=float(xy["lon"]),
                              file=cell_file))
        region_eval = evaluation[evaluation.region == region].to_dict("records") if not evaluation.empty and "region" in evaluation else []
        country_rhythm = (rhythm or {}).get("countries", {}).get(region)
        gate = (rhythm or {}).get("gate", {"decision": "insufficient_data"})
        rh = dict(country_rhythm, gate=gate) if country_rhythm else None
        payload = dict(meta=dict(region=region, name=region.replace("_", " "), label=label,
                       period_start=daily.date.min(), period_end=daily.date.max(), reference="MODIS Aqua",
                       model=" / ".join(sorted(agg.model.dropna().unique().astype(str))),
                       coverage_note=limitations[1], sources=[dict(name="NASA FIRMS archive", url="https://firms.modaps.eosdis.nasa.gov/country/")],
                       centroid=CENTROIDS.get(region, [0, 0]),
                       cell_count_total=total_cells, cell_count_displayed=len(cells),
                       cell_scope=f"{len(cells)} training-period-selected cells displayed out of {total_cells} occupied cells; region total uses all cells.",
                       limitations=limitations),
                       daily=daily.to_dict("records"), weekly_climatology=clim,
                       anomalies=anomalies, critical_periods=periods, rhythm=rh,
                       eval=region_eval, cells=cells)
        write_json(out / f"{region}.json", payload)
        daily.to_csv(out / f"{region}.csv", index=False)
        export_ics(periods, out / f"{region}.ics", dt.date.today().year + 1)
        regions.append(dict(id=region, name=region.replace("_", " "), file=f"{region}.json"))
    write_json(out / "index.json", dict(label=label, regions=regions,
               generated_at=dt.datetime.now(dt.timezone.utc).isoformat(), limitations=limitations))
    return regions
