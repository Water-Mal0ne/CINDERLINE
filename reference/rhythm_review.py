"""
Rhythm credibility checks after expert review (tasks B1, B2, B4, B5). None of these change the official decision.

python rhythm_review.py [data_dir] OUT_DIR

Uses kill_test.py's own loading, cleaning, local-time and per-year weekday index (imported, unchanged).
- B1  Monte Carlo precision: the official null test re-run with 200,000 draws (seed 20261114) per country x stream.
- B2  Leave-one-year-out rest-day index for the streams of the countries that passed (US, Australia, Brazil).
- B4  Negative control split: type 1 (volcano) and type 2 (other static land source), per country and stream.
- B5  Nepal power: real Nepal daily counts per stream; in each simulation every year's weekday labels are shifted
      by a random 0-6 days (keeps volume, seasonality and clustering, removes any real weekly signal), then a
      planted Saturday dip of 10% or 20% is applied by binomial thinning of Saturday detections. The official
      country rule is applied (rest day lowest and p < 0.05/21 in >= 2 of 3 streams; 5,000 null draws).
"""
import json
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kill_test as kt  # noqa: E402

LABEL = "REAL FIRMS DATA"
M_TESTS = 21
SEED = 20261114
N_NULL_BIG = 200_000
PASSED = ["United_States", "Australia", "Brazil"]


def yearly_matrix(sub):
    """Per-year normalised weekday rates, exactly as kill_test.weekday_index builds them."""
    this_year = kt.dt.date.today().year
    years, rows = [], []
    for year, y in sub.groupby("year"):
        year = int(year)
        if year >= this_year or len(y) < kt.MIN_DETECTIONS_PER_YEAR:
            continue
        if (y["file_year"] == year).mean() < 0.95:
            continue
        rate = np.bincount(y["weekday"].astype(int), minlength=7) / kt.weekday_exposure(year)
        rows.append(rate / rate.mean())
        years.append(year)
    return np.array(rows), years


def null_p(Y, rest_idx, n, rng):
    """Same null as kill_test: one random weekday per year, averaged; one-sided with +1 correction."""
    obs = Y.mean(axis=0)[rest_idx]
    exceed = 0
    chunk = 20_000
    for start in range(0, n, chunk):
        k = min(chunk, n - start)
        draws = Y[np.arange(len(Y))[None, :].repeat(k, 0), rng.integers(0, 7, (k, len(Y)))].mean(axis=1)
        exceed += int(np.sum(draws <= obs))
    return exceed, (exceed + 1) / (n + 1)


def b1_b2(veg, out):
    rng = np.random.default_rng(SEED)
    official = pd.read_csv("kill_test_results.csv")
    rows, loyo = [], []
    for country, cfg in kt.COUNTRIES.items():
        r = kt.DAYS.index(cfg["rest"])
        for stream in kt.STREAMS:
            sub = veg[(veg.country == country) & (veg.stream == stream)]
            Y, years = yearly_matrix(sub)
            off = official[(official.country == country) & (official.stream == stream) & (official.subset == "all")].iloc[0]
            if len(Y) < kt.MIN_YEARS:
                rows.append({"country": country, "stream": stream, "status": "insufficient_data"})
                continue
            exceed, p = null_p(Y, r, N_NULL_BIG, rng)
            se = np.sqrt(p * (1 - p) / N_NULL_BIG)
            mean = Y.mean(axis=0)
            lowest = bool(mean[r] == mean.min())
            sig = lowest and p < 0.05 / M_TESTS
            rows.append({"country": country, "stream": stream, "status": "ok", "years": len(Y),
                         "rest_day": cfg["rest"], "rest_index": round(float(mean[r]), 4), "rest_is_lowest": lowest,
                         "exceedances_200k": exceed, "p_200k": p, "mc_se": se,
                         "p_official_5000": float(off.p_null), "significant_200k": sig,
                         "significant_official": bool(off.significant), "call_changes": sig != bool(off.significant)})
            if country in PASSED:
                for i, yr in enumerate(years):
                    m = np.delete(Y, i, axis=0).mean(axis=0)
                    loyo.append({"country": country, "stream": stream, "left_out": yr,
                                 "rest_index": round(float(m[r]), 4), "lowest_day": kt.DAYS[int(m.argmin())],
                                 "rest_is_lowest": bool(m[r] == m.min())})
    b1 = pd.DataFrame(rows)
    b1.insert(0, "label", LABEL)
    b1.to_csv(os.path.join(out, "b1_monte_carlo_200k.csv"), index=False)
    lo = pd.DataFrame(loyo)
    lo.insert(0, "label", LABEL)
    lo.to_csv(os.path.join(out, "b2_leave_one_year_out.csv"), index=False)
    summary = lo.groupby(["country", "stream"]).agg(min_index=("rest_index", "min"), max_index=("rest_index", "max"),
                                                    always_lowest=("rest_is_lowest", "all"),
                                                    times_not_lowest=("rest_is_lowest", lambda s: int((~s).sum())))
    summary.to_csv(os.path.join(out, "b2_leave_one_year_out_summary.csv"))
    return b1, summary


def b4(static, out):
    rows = []
    for country, cfg in kt.COUNTRIES.items():
        r = kt.DAYS.index(cfg["rest"])
        for ftype, name in [(1, "type 1 (volcano)"), (2, "type 2 (other static land source)")]:
            for stream in kt.STREAMS:
                sub = static[(static.country == country) & (static.stream == stream) &
                             (static["type"].fillna(0).astype(int) == ftype)]
                res = kt.weekday_index(sub, r) if len(sub) else None
                row = {"country": country, "control": name, "stream": stream, "detections": int(len(sub))}
                if res is None:
                    row["status"] = "insufficient_data"
                else:
                    lo, hi = np.percentile(res["boots"][:, r], [2.5, 97.5])
                    m = res["mean"]
                    row.update(status="ok", years=res["years"], rest_day=cfg["rest"], rest_index=round(float(m[r]), 3),
                               ci95=f"{lo:.3f}-{hi:.3f}", p_null=res["p_null"], lowest_day=kt.DAYS[int(m.argmin())],
                               rest_is_lowest=bool(m[r] == m.min()),
                               significant_bonferroni21=bool(m[r] == m.min() and res["p_null"] < 0.05 / M_TESTS))
                rows.append(row)
    t = pd.DataFrame(rows)
    t.insert(0, "label", LABEL)
    t.to_csv(os.path.join(out, "b4_controls_by_type.csv"), index=False)
    return t


def b5(veg, out, sims=200):
    rng = np.random.default_rng(SEED + 5)
    sat = kt.DAYS.index("Sat")
    nepal = veg[veg.country == "Nepal"]
    daily = {}
    for stream in kt.STREAMS:
        sub = nepal[nepal.stream == stream]
        this_year = kt.dt.date.today().year
        per_year = {}
        for year, y in sub.groupby("year"):
            year = int(year)
            if year >= this_year or (y["file_year"] == year).mean() < 0.95:
                continue
            days = pd.date_range(f"{year}-01-01", f"{year}-12-31")
            counts = y.groupby(y["local"].dt.normalize()).size().reindex(days, fill_value=0).to_numpy()
            per_year[year] = (counts, days.dayofweek.to_numpy())
        daily[stream] = per_year
    results = []
    for dip in [0.0, 0.10, 0.20]:
        passes, stream_sig = 0, {s: 0 for s in kt.STREAMS}
        for _ in range(sims):
            n_sig = 0
            for stream in kt.STREAMS:
                rows = []
                for year, (counts, dow) in daily[stream].items():
                    shifted = (dow + rng.integers(0, 7)) % 7
                    c = counts.copy()
                    on_sat = shifted == sat
                    if dip > 0:
                        c[on_sat] = rng.binomial(c[on_sat], 1 - dip)
                    if c.sum() < kt.MIN_DETECTIONS_PER_YEAR:
                        continue
                    rate = np.bincount(shifted, weights=c, minlength=7) / kt.weekday_exposure(year)
                    rows.append(rate / rate.mean())
                if len(rows) < kt.MIN_YEARS:
                    continue
                Y = np.array(rows)
                _, p = null_p(Y, sat, kt.N_NULL, rng)
                m = Y.mean(axis=0)
                if m[sat] == m.min() and p < 0.05 / M_TESTS:
                    n_sig += 1
                    stream_sig[stream] += 1
            passes += n_sig >= kt.MIN_STREAMS_TO_CONFIRM
        results.append({"planted_saturday_dip": dip, "simulations": sims, "country_pass_rate": passes / sims,
                        **{f"{s}_significant_rate": stream_sig[s] / sims for s in kt.STREAMS}})
    t = pd.DataFrame(results)
    t.insert(0, "label", "SYNTHETIC PLANTED DIP ON REAL NEPAL VOLUME")
    t.to_csv(os.path.join(out, "b5_nepal_power.csv"), index=False)
    return t


def main():
    data_dir = sys.argv[1] if len(sys.argv) > 2 else "data"
    out = sys.argv[-1]
    os.makedirs(out, exist_ok=True)
    veg, static = kt.clean(kt.load(data_dir))
    veg = kt.add_local_time(veg, "vegetation")
    static = kt.add_local_time(static, "static_control")
    pd.set_option("display.width", 220)
    b1, b2s = b1_b2(veg, out)
    print("B1:\n" + b1.drop(columns=["label"]).to_string(index=False))
    print("\nB2:\n" + b2s.to_string())
    t4 = b4(static, out)
    print("\nB4:\n" + t4.drop(columns=["label"]).to_string(index=False))
    t5 = b5(veg, out)
    print("\nB5:\n" + t5.to_string(index=False))


if __name__ == "__main__":
    main()
