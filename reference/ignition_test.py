"""
ROBUSTNESS ANALYSIS (review E1): the rest-day test on new ignitions instead of raw detections.

python ignition_test.py [data_dir] OUT_DIR

An ignition event = a 0.25-degree grid cell that has at least one detection on a local civil day and none on the
previous day, per country and stream (cleaning, confidence filter and local time from kill_test.py, unchanged).
Each event is dated to that day. The weekday index, year bootstrap, null test, Bonferroni correction and gate are
kill_test.py's own functions applied to these events. Not part of the official decision.
"""
import json
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kill_test as kt  # noqa: E402

GRID = 0.25
LABEL = "REAL FIRMS DATA - IGNITION EVENTS (ROBUSTNESS)"


def ignitions(veg):
    v = veg.assign(cell=(np.floor(veg.latitude / GRID).astype("int32") * 10000 +
                         np.floor(veg.longitude / GRID).astype("int32")),
                   day=veg["local"].dt.normalize())
    cd = v.groupby(["country", "stream", "cell", "day"], observed=True).agg(file_year=("file_year", "min")).reset_index()
    cd = cd.sort_values(["country", "stream", "cell", "day"])
    prev = cd.groupby(["country", "stream", "cell"], observed=True)["day"].shift(1)
    new = prev.isna() | ((cd["day"] - prev).dt.days > 1)
    first_day = cd.groupby(["country", "stream"], observed=True)["day"].transform("min")
    ev = cd[new & (cd["day"] > first_day)].copy()      # the first day of a record cannot be judged
    ev["weekday"] = ev["day"].dt.day_of_week
    ev["year"] = ev["day"].dt.year
    return ev, cd


def main():
    data_dir = sys.argv[1] if len(sys.argv) > 2 else "data"
    out = sys.argv[-1]
    os.makedirs(out, exist_ok=True)
    veg, _ = kt.clean(kt.load(data_dir))
    veg = kt.add_local_time(veg, "vegetation")
    ev, cd = ignitions(veg)
    del veg
    res = kt.analyse(ev, "all")
    g = kt.gate(res, [])
    official = pd.read_csv("kill_test_results.csv")
    off = official[official.subset == "all"].set_index(["country", "stream"])
    res["detections_index_official"] = [off.rest_index.get((c, s), np.nan) for c, s in zip(res.country, res.stream)]
    res["ignition_events"] = res["detections"]
    res["cell_days"] = [int(((cd.country == c) & (cd.stream == s)).sum()) for c, s in zip(res.country, res.stream)]
    cols = ["country", "stream", "status", "years", "ignition_events", "cell_days", "rest_day", "rest_index",
            "rest_ci95", "lowest_day", "p_null", "significant", "detections_index_official"] + kt.DAYS
    table = res[[c for c in cols if c in res]].copy()
    table.insert(0, "label", LABEL)
    table.to_csv(os.path.join(out, "e1_ignition_results.csv"), index=False)
    g["label"] = LABEL
    g["note"] = "Robustness analysis on ignition events; not the official decision."
    json.dump(g, open(os.path.join(out, "e1_ignition_gate.json"), "w"), indent=2, default=str)
    pd.set_option("display.width", 220)
    print(table.drop(columns=["label"] + kt.DAYS).to_string(index=False))
    print("\nIgnition gate (robustness only):", g["decision"], {c: v["status"] for c, v in g["per_country"].items()})


if __name__ == "__main__":
    main()
