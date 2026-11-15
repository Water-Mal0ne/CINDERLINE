"""NOAA-20 VIIRS as a separate-platform transfer check (review E3). Not part of the official decision or the released model.

python -m pipeline.review.noaa20_check NOAA20_DATA_DIR [--out reports/review/noaa20]

NOAA20_DATA_DIR holds FIRMS country archives viirs-jpss1/{year}/viirs-jpss1_{year}_{Country}.csv (2018-2024).
Countries with all seven years present are analysed.

(a) Conversion check: NOAA-20 vegetation detections (type 0, confidence n/h, local civil date as in kill_test.py) are
    converted to the Aqua reference scale with the SAVED seven-country model, no refitting: the selected model per
    country (B1 global ratio, or M1 country x day/night x FRP-class ratios fitted on S-NPP). Weekly (W-MON) series are
    compared with the published converted S-NPP series and with observed Aqua, 2018-2024 and test years 2020-2024.
(b) Fourth rhythm stream: the kill_test.py weekday index, year bootstrap and null test on NOAA-20 detections, reported
    separately with the same 0.05/21 threshold for comparison; not added to the official gate.

This checks transfer between related measurement products, not independent ground-truth accuracy.
Shared discrepancy against Aqua does not diagnose its cause. A strict common-date outage sensitivity
remains unfinished: partly masked S-NPP weeks can be compared with fuller NOAA-20 weeks.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from pipeline.harmonize import _strata, metrics, predict_counts
from pipeline.review.harmonization_review import COUNTRIES, national_daily

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "reference"))
import kill_test as kt  # noqa: E402

YEARS = list(range(2018, 2025))
TEST = list(range(2020, 2025))
LABEL = "REAL FIRMS DATA - NOAA-20 VIIRS CHECK"


def load(data_dir: Path, country: str) -> pd.DataFrame | None:
    paths = [data_dir / "viirs-jpss1" / str(y) / f"viirs-jpss1_{y}_{country}.csv" for y in YEARS]
    if not all(p.exists() and p.stat().st_size > 0 for p in paths):
        return None
    frames = []
    for y, p in zip(YEARS, paths):
        d = pd.read_csv(p, usecols=lambda c: c in {"latitude", "longitude", "acq_date", "acq_time", "confidence",
                                                   "type", "daynight", "frp"}, low_memory=False)
        d["file_year"], d["country"] = y, country
        frames.append(d)
    d = pd.concat(frames, ignore_index=True)
    d = d[(d["type"].fillna(0).astype(int) == 0) & d["confidence"].astype(str).str.lower().isin(["n", "h"])]
    d = d.assign(stream="VIIRS")
    return kt.add_local_time(d, f"noaa20_{country}")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("data_dir")
    ap.add_argument("--out", default="reports/review/noaa20")
    a = ap.parse_args()
    out = ROOT / a.out
    out.mkdir(parents=True, exist_ok=True)
    model = json.loads((ROOT / "reports/harmonization_model.json").read_text(encoding="utf-8"))
    conv_rows, rhythm_rows, done = [], [], []
    for country in COUNTRIES:
        n20 = load(Path(a.data_dir), country)
        if n20 is None:
            continue
        done.append(country)
        sel = model["selection"][country]["selected"]
        n20["date"] = n20["local"].dt.normalize()
        n20["stratum"] = _strata(n20)
        counts = n20.groupby(["date", "stratum"]).size().rename("n").reset_index()
        counts["country"] = country
        counts["pred"] = predict_counts(counts, sel, model["ratios"])
        n20_conv = counts.groupby("date").pred.sum()
        n20_raw = counts.groupby("date").n.sum()
        daily, _ = national_daily(country)
        frame = pd.DataFrame({"aqua": daily.raw_aqua, "snpp_converted": daily.harmonized.where(daily.source == "converted VIIRS"),
                              "snpp_raw": daily.raw_viirs})
        frame = frame[(frame.index.year >= 2018) & (frame.index.year <= 2024)]
        frame["n20_converted"] = n20_conv.reindex(frame.index).fillna(0)
        frame["n20_raw"] = n20_raw.reindex(frame.index).fillna(0)
        for period, yrs in [("2018-2024", YEARS), ("test 2020-2024", TEST)]:
            f = frame[frame.index.year.isin(yrs)]
            w = f.resample("W-MON").sum(min_count=1).dropna(subset=["aqua", "snpp_converted"])
            for ref in ["snpp_converted", "aqua"]:
                m = metrics(w[ref], w["n20_converted"])
                conv_rows.append({"country": country, "model": sel, "period": period, "reference": ref, "weeks": len(w),
                                  "bias_pct": m["bias_pct"], "mae": m["mae"], "correlation": m["correlation"]})
            m = metrics(w["aqua"], w["snpp_converted"])
            conv_rows.append({"country": country, "model": sel, "period": period, "reference": "aqua (S-NPP converted, for comparison)",
                              "weeks": len(w), "bias_pct": m["bias_pct"], "mae": m["mae"], "correlation": m["correlation"]})
            conv_rows[-1]["raw_ratio_n20_per_snpp"] = float(f.n20_raw.sum() / f.snpp_raw.sum())
        # weekly figure
        w = frame.resample("W-MON").sum(min_count=1)
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots(figsize=(11, 4))
        ax.plot(w.index, w.aqua, color="#1c7ed6", lw=1.0, label="observed MODIS Aqua")
        ax.plot(w.index, w.snpp_converted, color="#e8590c", lw=1.0, label=f"S-NPP converted ({sel}, released)")
        ax.plot(w.index, w.n20_converted, color="#2b8a3e", lw=1.0, alpha=0.85, label=f"NOAA-20 converted (same {sel} ratios)")
        ax.set_yscale("symlog", linthresh=10)
        ax.set_title(f"[{LABEL}]  {country.replace('_', ' ')}: weekly Aqua-reference-equivalent detections, 2018-2024", fontsize=10)
        ax.legend(fontsize=8)
        fig.tight_layout()
        fig.savefig(out / f"noaa20_vs_snpp_{country}.png", dpi=110)
        plt.close(fig)
        # (b) rhythm, fourth stream
        rest = kt.DAYS.index(kt.COUNTRIES[country]["rest"])
        res = kt.weekday_index(n20, rest)
        if res is None:
            rhythm_rows.append({"country": country, "status": "insufficient_data", "detections": len(n20)})
        else:
            lo, hi = np.percentile(res["boots"][:, rest], [2.5, 97.5])
            m = res["mean"]
            rhythm_rows.append({"country": country, "status": "ok", "years": res["years"], "detections": len(n20),
                                "rest_day": kt.COUNTRIES[country]["rest"], "rest_index": round(float(m[rest]), 3),
                                "ci95": f"{lo:.3f}-{hi:.3f}", "lowest_day": kt.DAYS[int(m.argmin())],
                                "p_null": res["p_null"], "significant_at_0.05_over_21": bool(m[rest] == m.min() and res["p_null"] < 0.05 / 21),
                                **{d: round(float(v), 3) for d, v in zip(kt.DAYS, m)}})
    c = pd.DataFrame(conv_rows)
    c.insert(0, "label", LABEL)
    c.to_csv(out / "noaa20_conversion_check.csv", index=False)
    r = pd.DataFrame(rhythm_rows)
    r.insert(0, "label", LABEL)
    r.to_csv(out / "noaa20_rhythm_stream.csv", index=False)
    pd.set_option("display.width", 220)
    print("countries analysed:", done)
    print(c.drop(columns=["label"]).round(3).to_string(index=False))
    print(r.drop(columns=["label"]).to_string(index=False))


if __name__ == "__main__":
    main()
