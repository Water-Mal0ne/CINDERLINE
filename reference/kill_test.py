"""
FIRETRACE kill test: do fire detections dip on each country's local rest day?

Run after download.py:   python kill_test.py [data_dir] [--label "REAL FIRMS DATA"]
Needs: pandas, numpy, matplotlib, timezonefinder

Method
- Main analysis: vegetation fires only (FIRMS type 0), low-confidence detections dropped.
  Static/volcano detections (type 1, 2) are kept in a separate branch as a negative control.
- UTC acquisition time is converted to local CIVIL time (IANA zones). Rows whose zone
  cannot be resolved or whose timestamp is invalid are excluded and counted.
- Terra, Aqua and VIIRS are separate streams. They watch overlapping fires, so agreement
  between them is corroboration, not independent replication.
- Per complete calendar year: weekday rate = detections on that weekday / number of times
  that weekday occurs in the year (52 or 53); index = rate / mean rate. 1.00 = average.
- Mean over years; 95% CI by bootstrapping whole years.
- Null test: under "no weekly effect", the rest day is just a random weekday each year.
  p = share of 5000 draws (one random weekday per year, averaged) that are as low as observed.
- Multiple comparisons: Bonferroni over all country x stream tests in the main analysis.

Outputs: kill_test_results.csv, kill_test_gate.json, kill_test_diagnostics.json, kill_test.png
Limitation: cloud cover and overpass coverage are NOT measured here. Day-of-week bias in
coverage is unlikely over many years but untested; the negative control is the check.
"""
import argparse
import datetime as dt
import glob
import json
import os
import sys

import numpy as np
import pandas as pd

DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
STREAMS = ["Terra", "Aqua", "VIIRS"]

# Predicted rest day, fixed BEFORE looking at results. tz None = look up per location.
COUNTRIES = {
    "United_States": {"rest": "Sun", "tz": None},
    "Australia":     {"rest": "Sun", "tz": None},
    "Brazil":        {"rest": "Sun", "tz": None},
    "India":         {"rest": "Sun", "tz": "Asia/Kolkata"},
    "Nepal":         {"rest": "Sat", "tz": "Asia/Kathmandu"},
    "Bangladesh":    {"rest": "Fri", "tz": "Asia/Dhaka"},
    "Egypt":         {"rest": "Fri", "tz": "Africa/Cairo"},
}
CONTROL_COUNTRY = "United_States"
MIN_DETECTIONS_PER_YEAR = 140
MIN_YEARS = 5
MIN_STREAMS_TO_CONFIRM = 2
N_BOOT, N_NULL = 2000, 5000
rng = np.random.default_rng(42)
USE_COLS = {"latitude", "longitude", "acq_date", "acq_time", "satellite", "instrument",
            "confidence", "type", "daynight"}
CAT_COLS = ["acq_date", "satellite", "instrument", "confidence", "daynight", "country"]
diag = {}


def load(data_dir):
    frames = []
    for path in sorted(glob.glob(os.path.join(data_dir, "**", "*.csv"), recursive=True)):
        base = os.path.basename(path)[:-4]
        parts = base.split("_", 2)
        if len(parts) < 3:
            continue
        # memory: keep only the columns the analysis uses; repeated text as categories
        df = pd.read_csv(path, low_memory=False, usecols=lambda c: c in USE_COLS)
        df["country"] = parts[2]
        df["file_year"] = int(parts[1])
        for c in CAT_COLS:
            if c in df:
                df[c] = df[c].astype(str).astype("category")
        frames.append(df)
    if not frames:
        sys.exit(f"No FIRMS CSV files found under {data_dir}/")
    # identical categories in every frame, so concat keeps the compact dtype
    for c in CAT_COLS:
        cats = sorted(set().union(*(f[c].cat.categories for f in frames if c in f)))
        for f in frames:
            if c in f:
                f[c] = f[c].cat.set_categories(cats)
    diag["files"] = len(frames)
    df = pd.concat(frames, ignore_index=True)
    del frames
    diag["rows_loaded"] = int(len(df))
    return df


def clean(df):
    inst = df["instrument"].astype(str).str.upper()
    sat = df["satellite"].astype(str).str.upper()
    df = df.assign(stream=np.where(inst.str.contains("VIIRS"), "VIIRS",
                          np.where(sat.str.startswith("T"), "Terra",
                          np.where(sat.str.startswith("A"), "Aqua", "other"))))
    conf = df["confidence"].astype(str).str.lower()
    viirs = df["stream"] == "VIIRS"
    ok = (viirs & conf.isin(["n", "h", "nominal", "high"])) | \
         (~viirs & (pd.to_numeric(df["confidence"].astype(str), errors="coerce") >= 30))
    df = df[ok & (df["stream"] != "other")]
    ftype = df["type"].fillna(0).astype(int) if "type" in df.columns else pd.Series(0, index=df.index)
    veg, static = df[ftype == 0], df[ftype.isin([1, 2])]
    diag["rows_usable_confidence"] = int(len(df))
    diag["rows_vegetation"] = int(len(veg))
    diag["rows_static_control"] = int(len(static))
    return veg, static


def add_local_time(df, label):
    if df.empty:
        return df.assign(local=pd.NaT, weekday=np.nan, year=np.nan)
    t = pd.to_numeric(df["acq_time"], errors="coerce").astype("Int64").astype(str).str.zfill(4)
    utc = pd.to_datetime(df["acq_date"].astype(str) + " " + t, format="%Y-%m-%d %H%M",
                         utc=True, errors="coerce")
    bad_ts = int(utc.isna().sum())
    df = df.assign(utc=utc)[utc.notna()]
    local = pd.Series(pd.NaT, index=df.index, dtype="datetime64[ns]")
    tf, cache = None, {}
    for country, grp in df.groupby("country"):
        tz = COUNTRIES.get(country, {}).get("tz")
        if tz:
            local.loc[grp.index] = grp["utc"].dt.tz_convert(tz).dt.tz_localize(None)
            continue
        if tf is None:
            try:
                from timezonefinder import TimezoneFinder
            except ImportError:
                sys.exit("timezonefinder is required for multi-zone countries: pip install timezonefinder")
            tf = TimezoneFinder()
        keys = list(zip(grp["latitude"].round(1), grp["longitude"].round(1)))
        for k in set(keys):
            if k not in cache:
                cache[k] = tf.timezone_at(lat=k[0], lng=k[1]) or tf.closest_timezone_at(lat=k[0], lng=k[1])
        zones = pd.Series([cache[k] for k in keys], index=grp.index)
        for zone, sub in grp.groupby(zones):
            local.loc[sub.index] = sub["utc"].dt.tz_convert(zone).dt.tz_localize(None)
    unresolved = int(local.isna().sum())
    df = df.assign(local=local)[local.notna()]
    changed = float((df["local"].dt.date != df["utc"].dt.date).mean())
    diag[label] = {"invalid_timestamps_dropped": bad_ts, "unresolved_timezone_dropped": unresolved,
                   "share_date_changed_by_utc_to_local": round(changed, 4)}
    return df.assign(weekday=df["local"].dt.day_of_week, year=df["local"].dt.year)


def weekday_exposure(year):
    days = pd.date_range(f"{year}-01-01", f"{year}-12-31", freq="D")
    return np.bincount(days.day_of_week, minlength=7).astype(float)


def weekday_index(sub, rest_idx):
    this_year = dt.date.today().year
    yearly = []
    for year, y in sub.groupby("year"):
        year = int(year)
        # complete calendar years only; the edge years get few rows from UTC->local spill
        if year >= this_year or len(y) < MIN_DETECTIONS_PER_YEAR:
            continue
        if (y["file_year"] == year).mean() < 0.95:
            continue
        rate = np.bincount(y["weekday"].astype(int), minlength=7) / weekday_exposure(year)
        yearly.append(rate / rate.mean())
    if len(yearly) < MIN_YEARS:
        return None
    Y = np.array(yearly)
    n = len(Y)
    boots = Y[rng.integers(0, n, (N_BOOT, n))].mean(axis=1)
    null = Y[np.arange(n)[None, :].repeat(N_NULL, 0), rng.integers(0, 7, (N_NULL, n))].mean(axis=1)
    mean = Y.mean(axis=0)
    p = float((np.sum(null <= mean[rest_idx]) + 1) / (N_NULL + 1))
    return {"mean": mean, "boots": boots, "years": n, "p_null": p}


def analyse(df, subset_name):
    rows = []
    for country, cfg in COUNTRIES.items():
        r = DAYS.index(cfg["rest"])
        for stream in STREAMS:
            sub = df[(df["country"] == country) & (df["stream"] == stream)]
            if subset_name == "day" and "daynight" in sub.columns:
                sub = sub[sub["daynight"] == "D"]
            res = weekday_index(sub, r)
            if res is None:
                rows.append({"country": country, "subset": subset_name, "stream": stream,
                             "status": "insufficient_data", "detections": int(len(sub))})
                continue
            lo, hi = np.percentile(res["boots"], [2.5, 97.5], axis=0)
            rows.append({
                "country": country, "subset": subset_name, "stream": stream,
                "status": "ok", "years": res["years"], "detections": int(len(sub)),
                "rest_day": cfg["rest"], "rest_index": round(res["mean"][r], 3),
                "rest_ci95": f"{lo[r]:.3f}-{hi[r]:.3f}", "rest_ci_hi": hi[r],
                "lowest_day": DAYS[int(res["mean"].argmin())],
                "rest_is_lowest": bool(res["mean"][r] == res["mean"].min()),
                "p_null": res["p_null"],
                **{d: round(v, 3) for d, v in zip(DAYS, res["mean"])},
                "_lo": lo, "_hi": hi,
            })
    out = pd.DataFrame(rows)
    ok = out["status"] == "ok"
    m = max(int(ok.sum()), 1)
    out["bonferroni_m"] = m
    out["significant"] = ok & (out.get("p_null", 1) < 0.05 / m) & out.get("rest_is_lowest", False)
    return out


def negative_control(static):
    """Static sources (gas flares, volcanoes, industry) have no reason to follow a rest day
    in the way field burning does. Pooled per stream across all countries."""
    res = []
    for stream in STREAMS:
        sub = static[static["stream"] == stream]
        if len(sub) < 1000:
            res.append({"stream": stream, "status": "insufficient_data", "detections": int(len(sub))})
            continue
        counts = np.bincount(sub["weekday"].astype(int), minlength=7).astype(float)
        idx = counts / counts.mean()
        res.append({"stream": stream, "status": "ok", "detections": int(len(sub)),
                    "max_abs_deviation": round(float(np.abs(idx - 1).max()), 3),
                    **{d: round(v, 3) for d, v in zip(DAYS, idx)}})
    return res


def gate(main, controls):
    def country_status(c):
        rows = main[main.country == c]
        okr = rows[rows.status == "ok"]
        if len(okr) < MIN_STREAMS_TO_CONFIRM:
            return "insufficient_data", 0, len(okr)
        n_sig = int(okr.significant.sum())
        return ("pass" if n_sig >= MIN_STREAMS_TO_CONFIRM else "fail"), n_sig, len(okr)

    per_country = {}
    for c in COUNTRIES:
        s, n_sig, n_ok = country_status(c)
        per_country[c] = {"status": s, "streams_significant": n_sig, "streams_with_data": n_ok,
                          "predicted_rest_day": COUNTRIES[c]["rest"]}
    us = per_country[CONTROL_COUNTRY]["status"]
    others = [c for c, v in per_country.items() if c != CONTROL_COUNTRY and v["status"] == "pass"]
    tested_others = [c for c, v in per_country.items()
                     if c != CONTROL_COUNTRY and v["status"] != "insufficient_data"]
    if us == "insufficient_data" or len(tested_others) < 2:
        decision = "insufficient_data"
    elif us == "pass" and len(others) >= 2:
        decision = "pass"
    else:
        decision = "fail"
    return {
        "decision": decision,
        "rule": (f"{CONTROL_COUNTRY} replication must pass AND >=2 other countries pass; a country "
                 f"passes when its predicted rest day is the lowest weekday with Bonferroni-adjusted "
                 f"null-test p < 0.05/m in >= {MIN_STREAMS_TO_CONFIRM} streams"),
        "replication_check": {"country": CONTROL_COUNTRY, "status": us,
                              "note": "A fail here means investigate data, method and comparability "
                                      "with Earl et al. 2015; it is not by itself proof of a bug."},
        "countries_passing": others,
        "per_country": per_country,
        "negative_control_static_sources": controls,
        "caveats": [
            "A robust rest-day dip is consistent with human scheduling of burning; it does not by "
            "itself establish ignition cause. Absence of a dip does not establish weather-driven fire.",
            "Streams observe overlapping fires: agreement is corroboration, not independent replication.",
            "Observation coverage (cloud, overpass gaps) by weekday is not measured.",
        ],
    }


def plot(res, label):
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        print("matplotlib not installed, skipping chart.")
        return
    res = res[res.status == "ok"]
    countries = list(dict.fromkeys(res.country))
    if not countries:
        return
    ylo = min(0.8, float(np.min(np.vstack(res["_lo"].values))) - 0.03)
    yhi = max(1.15, float(np.max(np.vstack(res["_hi"].values))) + 0.03)
    fig, axes = plt.subplots(len(countries), 3, figsize=(12, 2.6 * len(countries) + 0.8),
                             sharey=True, squeeze=False)
    for i, country in enumerate(countries):
        for j, stream in enumerate(STREAMS):
            ax = axes[i][j]
            row = res[(res.country == country) & (res.stream == stream)]
            if row.empty:
                ax.set_axis_off()
                continue
            row = row.iloc[0]
            vals = np.array([row[d] for d in DAYS])
            err = np.array([vals - row["_lo"], row["_hi"] - vals])
            colors = ["#d9480f" if d == row["rest_day"] else "#adb5bd" for d in DAYS]
            ax.bar(DAYS, vals, yerr=err, color=colors, capsize=2)
            ax.axhline(1, color="black", lw=0.6)
            ax.set_ylim(ylo, yhi)
            mark = " *" if row["significant"] else ""
            ax.set_title(f"{country} - {stream} ({int(row['years'])} yrs){mark}", fontsize=9)
    fig.suptitle(f"[{label}]  Fire detections by local weekday (1.0 = average; "
                 f"orange = predicted rest day; * = significant after correction)", fontsize=10)
    if "SYNTHETIC" in label.upper():
        fig.text(0.5, 0.5, "SYNTHETIC DATA", fontsize=60, color="red", alpha=0.15,
                 ha="center", va="center", rotation=25)
    fig.tight_layout(rect=[0, 0, 1, 0.98])
    fig.savefig("kill_test.png", dpi=120)
    print("Chart saved to kill_test.png")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("data_dir", nargs="?", default="data")
    ap.add_argument("--label", default="REAL FIRMS DATA")
    a = ap.parse_args()
    diag["label"] = a.label

    veg, static = clean(load(a.data_dir))
    veg = add_local_time(veg, "vegetation")
    static = add_local_time(static, "static_control")

    res = pd.concat([analyse(veg, "all"), analyse(veg, "day")], ignore_index=True)
    main_res = res[res.subset == "all"]
    g = gate(main_res, negative_control(static))
    g["label"] = a.label

    # output only: per-weekday 95% bootstrap CI bounds (same bootstrap as rest_ci95)
    out = res.copy()
    for i, d in enumerate(DAYS):
        for k in ("lo", "hi"):
            out[f"{d}_{k}"] = [round(float(v[i]), 3) if isinstance(v, np.ndarray) else np.nan
                               for v in out.get(f"_{k}", pd.Series([None] * len(out)))]
    out.drop(columns=[c for c in ["_lo", "_hi", "rest_ci_hi"] if c in out], errors="ignore") \
       .to_csv("kill_test_results.csv", index=False)
    json.dump(g, open("kill_test_gate.json", "w"), indent=2, default=str)
    json.dump(diag, open("kill_test_diagnostics.json", "w"), indent=2)

    pd.set_option("display.width", 170)
    show = ["country", "stream", "status", "years", "detections", "rest_day", "rest_index",
            "rest_ci95", "lowest_day", "p_null", "significant"]
    print(f"[{a.label}]  diagnostics: {json.dumps(diag)}\n")
    for subset in ["all", "day"]:
        print(f"=== {'All detections' if subset == 'all' else 'Daytime only'} ===")
        print(res[res.subset == subset][[c for c in show if c in res]].to_string(index=False), "\n")
    print("=== Negative control (static sources) ===")
    for c in g["negative_control_static_sources"]:
        print(" ", c)
    print("\n=== Gate ===")
    for c, v in g["per_country"].items():
        print(f"  {c:14s} {v['status']:18s} {v['streams_significant']}/{v['streams_with_data']} streams")
    print(f"\nDECISION: {g['decision'].upper()}   (details in kill_test_gate.json)")
    plot(main_res, a.label)


if __name__ == "__main__":
    main()
