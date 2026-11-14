"""Year-level recheck of the two static-source controls that dip on Sunday (review follow-up). Report only.

python -m pipeline.review.control_check [RAW_DATA_DIR] [--out reports/review/controls]

Controls: US type 1 (volcano) per stream, and Brazil type 2 (other static land source) Terra; every other stream of
both controls is shown for context. Method is the official one (kill_test.py / pipeline.rhythm.analyse_stream):
each complete calendar year with >= 140 detections gives a weekday index (counts / weekday exposure, normalised to
mean 1); the index is the mean over years; 95% CI from a year bootstrap; p from the random-weekday null (one random
weekday per year, averaged), one-sided, +1 correction, with 200,000 draws; Bonferroni 0.05/21; at least 5 years.
No pooling of counts across years.

Input: data/sample/seven_country_rhythm_counts.parquet (year x weekday x type counts on local civil dates, the table
behind the 2002-2024 robustness run). Eligible years per stream are those the 2002-2024 robustness run used
(reports/rhythm_results.json year_list), so partial archive years are excluded the same way. Periods: 2002-2024
(the robustness run) and 2013-2024 (the official kill_test.py window).

Sensitivity: leave out the single year with the most detections; full leave-one-year-out range.
Where: if RAW_DATA_DIR (FIRMS country CSVs, modis/ and viirs-snpp/, 2013-2024) is given, US type 1 detections are
assigned to named volcano areas by location, with per-year and per-month counts, and the VIIRS test is repeated
without Hawaii and without Kilauea's 2018 eruption year.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
SUN = 6
MIN_PER_YEAR, MIN_YEARS, M = 140, 5, 21
N_NULL, N_BOOT, SEED = 200_000, 5_000, 20261114
LABEL = "REAL FIRMS DATA - CONTROL RECHECK (robustness, not part of the official decision)"
# rough boxes (lat_min, lat_max, lon_min, lon_max); first match wins
AREAS = [
    ("Kilauea (Hawaii)", 19.0, 19.6, -155.45, -154.75),
    ("Mauna Loa (Hawaii)", 19.2, 19.8, -155.8, -155.45),
    ("other Hawaii", 18.5, 22.5, -161.0, -154.5),
    ("Alaska / Aleutians", 50.0, 72.0, -180.0, -129.0),
    ("Alaska (west of 180)", 50.0, 56.0, 165.0, 180.0),
]


def exposure(year):
    days = pd.date_range(f"{year}-01-01", f"{year}-12-31", freq="D")
    return np.bincount(days.day_of_week, minlength=7).astype(float)


def year_matrix(counts):
    """counts: DataFrame year x weekday (7 columns). Returns per-year indices, years and detections."""
    rows, years, dets = [], [], []
    for year, c in counts.iterrows():
        c = c.to_numpy(float)
        if c.sum() < MIN_PER_YEAR:
            continue
        rate = c / exposure(int(year))
        rows.append(rate / rate.mean())
        years.append(int(year))
        dets.append(int(c.sum()))
    return np.array(rows), years, dets


def test(Y, rng):
    n = len(Y)
    mean = Y.mean(axis=0)
    boots = Y[rng.integers(0, n, (N_BOOT, n))].mean(axis=1)
    lo, hi = np.percentile(boots[:, SUN], [2.5, 97.5])
    exceed = 0
    for start in range(0, N_NULL, 20_000):
        k = min(20_000, N_NULL - start)
        draws = Y[np.arange(n)[None, :], rng.integers(0, 7, (k, n))].mean(axis=1)
        exceed += int(np.sum(draws <= mean[SUN]))
    p = (exceed + 1) / (N_NULL + 1)
    lowest = bool(mean[SUN] == mean.min())
    return {"sun_index": round(float(mean[SUN]), 3), "ci95": f"{lo:.3f}-{hi:.3f}", "ci_upper_below_1": bool(hi < 1),
            "lowest_day": DAYS[int(mean.argmin())], "p_null": p, "p_bonferroni21": min(p * M, 1.0),
            "significant_0.05_over_21": bool(lowest and p < 0.05 / M)}


def run_one(name, counts, rng):
    Y, years, dets = year_matrix(counts)
    row = {"control": name, "eligible_years": int(len(counts)), "years_with_140plus": len(Y),
           "years_used": " ".join(map(str, years)), "detections_used": int(sum(dets))}
    if len(Y) < MIN_YEARS:
        return {**row, "status": "insufficient_data"}, None
    row.update(status="ok", **test(Y, rng))
    big = int(np.argmax(dets))
    row["largest_year"], row["largest_year_share"] = years[big], round(dets[big] / sum(dets), 3)
    if len(Y) - 1 >= MIN_YEARS:
        r2 = test(np.delete(Y, big, axis=0), rng)
        row.update({f"without_largest_{k}": v for k, v in r2.items()})
    loyo = [np.delete(Y, i, axis=0).mean(axis=0) for i in range(len(Y))]
    row["loyo_sun_min"] = round(min(m[SUN] for m in loyo), 3)
    row["loyo_sun_max"] = round(max(m[SUN] for m in loyo), 3)
    row["loyo_times_sun_not_lowest"] = int(sum(m[SUN] != m.min() for m in loyo))
    per_year = pd.DataFrame({"control": name, "year": years, "detections": dets,
                             "sun_index": np.round(Y[:, SUN], 3), "lowest_day": [DAYS[int(i)] for i in Y.argmin(axis=1)]})
    return row, per_year


def counts_table(t, country, stream, ftype, years):
    s = t[(t.country == country) & (t.stream == stream) & (t.type == ftype) & t.year.isin(years)]
    c = s.groupby(["year", "weekday"]).n.sum().unstack(fill_value=0).reindex(columns=range(7), fill_value=0)
    return c.reindex(sorted(years), fill_value=0)


def area(lat, lon):
    out = np.full(len(lat), "other US", dtype=object)
    for name, a, b, c, d in reversed(AREAS):
        out[(lat >= a) & (lat <= b) & (lon >= c) & (lon <= d)] = name
    return out


def raw_us_volcano(raw):
    import sys
    sys.path.insert(0, str(ROOT / "reference"))
    import kill_test as kt
    frames = []
    for sub, stream in [("modis", None), ("viirs-snpp", "VIIRS")]:
        for p in sorted((raw / sub).glob("*/*_United_States.csv")):
            d = pd.read_csv(p, low_memory=False)
            d = d[d["type"].fillna(0).astype(int) == 1].copy()
            if d.empty:
                continue
            d["file_year"], d["country"] = int(p.parent.name), "United_States"
            frames.append(d)
    d = pd.concat(frames, ignore_index=True)
    veg, static = kt.clean(d)
    static = kt.add_local_time(static, "us_volcano")
    static["area"] = area(static.latitude.to_numpy(), static.longitude.to_numpy())
    static["month"] = static.local.dt.to_period("M").astype(str)
    return static


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("raw", nargs="?")
    ap.add_argument("--out", default="reports/review/controls")
    a = ap.parse_args()
    out = ROOT / a.out
    out.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(SEED)
    t = pd.read_parquet(ROOT / "data/sample/seven_country_rhythm_counts.parquet")
    saved = {(r["country"], r["stream"]): r["year_list"]
             for r in json.loads((ROOT / "reports/rhythm_results.json").read_text(encoding="utf-8"))["controls"]}
    rows, per_year = [], []
    jobs = [("United_States", s, 1, "US type 1 (volcano)") for s in ["Terra", "Aqua", "VIIRS"]]
    jobs += [("United_States", s, 2, "US type 2 (other static)") for s in ["Terra", "Aqua", "VIIRS"]]
    jobs += [("Brazil", s, 2, "Brazil type 2 (other static)") for s in ["Terra", "Aqua", "VIIRS"]]
    for country, stream, ftype, name in jobs:
        for period, keep in [("2002-2024", lambda y: True), ("2013-2024", lambda y: y >= 2013)]:
            years = [y for y in saved[(country, stream)] if keep(y)]
            row, py = run_one(f"{name} {stream} {period}", counts_table(t, country, stream, ftype, years), rng)
            rows.append({"country": country, "stream": stream, "type": ftype, "period": period, **row})
            if py is not None:
                per_year.append(py)
    for period, years in [("2002-2007", range(2002, 2008)), ("2002-2012", range(2002, 2013)),
                          ("2008-2024", range(2008, 2025))]:
        row, _ = run_one(f"Brazil type 2 (other static) Terra {period}",
                         counts_table(t, "Brazil", "Terra", 2, list(years)), rng)
        rows.append({"country": "Brazil", "stream": "Terra", "type": 2, "period": period, **row})
    res = pd.DataFrame(rows)
    res.insert(0, "label", LABEL)
    res.to_csv(out / "control_recheck.csv", index=False)
    pd.concat(per_year).assign(label=LABEL).to_csv(out / "control_recheck_per_year.csv", index=False)
    pd.set_option("display.width", 250)
    cols = ["control", "years_with_140plus", "detections_used", "sun_index", "ci95", "lowest_day", "p_null",
            "significant_0.05_over_21", "largest_year", "largest_year_share", "without_largest_sun_index",
            "without_largest_ci95", "without_largest_p_null", "without_largest_significant_0.05_over_21",
            "loyo_sun_min", "loyo_sun_max", "loyo_times_sun_not_lowest"]
    print(res[[c for c in cols if c in res]].to_string(index=False))
    print(pd.concat(per_year).to_string(index=False))

    if a.raw:
        v = raw_us_volcano(Path(a.raw))
        by_area = v.groupby(["stream", "area"]).size().unstack(fill_value=0)
        by_year = v.groupby(["stream", "year", "area"]).size().unstack(fill_value=0)
        months = (v.groupby(["stream", "month", "area"]).size().rename("detections").reset_index()
                  .sort_values("detections", ascending=False).groupby("stream").head(12))
        by_area.to_csv(out / "us_volcano_by_area.csv")
        by_year.to_csv(out / "us_volcano_by_year_area.csv")
        months.to_csv(out / "us_volcano_top_months.csv", index=False)
        print(by_area.to_string(), by_year.to_string(), months.to_string(index=False), sep="\n\n")
        extra = []
        vi = v[v.stream == "VIIRS"]
        for name, sub in [("VIIRS 2013-2024 raw CSVs, all areas", vi),
                          ("VIIRS without Hawaii", vi[~vi.area.str.contains("Hawaii")]),
                          ("VIIRS Hawaii only", vi[vi.area.str.contains("Hawaii")]),
                          ("VIIRS Alaska only", vi[vi.area.str.startswith("Alaska")]),
                          ("VIIRS without Kilauea 2018", vi[~((vi.area == "Kilauea (Hawaii)") & (vi.year == 2018))])]:
            sub = sub[sub.file_year == sub.year]
            c = sub.groupby(["year", "weekday"]).size().unstack(fill_value=0).reindex(columns=range(7), fill_value=0)
            row, _ = run_one(name, c, rng)
            extra.append(row)
        e = pd.DataFrame(extra)
        e.insert(0, "label", LABEL)
        e.to_csv(out / "us_volcano_by_area_tests.csv", index=False)
        print(e[[c for c in cols if c in e]].to_string(index=False))


if __name__ == "__main__":
    main()
