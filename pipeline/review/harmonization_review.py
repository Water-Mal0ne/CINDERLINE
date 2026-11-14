"""Harmonization evidence for review (tasks A1-A5). Nothing is refitted or re-selected.

python -m pipeline.review.harmonization_review [--out reports/review]

Inputs (all committed): reports/harmonization_eval.csv, reports/harmonization_model.json and the published
national daily series in web/public/data/{country}.json (observed Aqua, raw VIIRS and the selected model's
converted VIIRS). B0 = raw VIIRS and B1 = raw VIIRS x the saved global ratio are exact transforms of the
published daily VIIRS, so they are recomputed here; M1 is available from published data only where it is the
selected model. Weekly = pandas 'W-MON' weeks, the definition used by harmonize._evaluate for the official table.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from pipeline.harmonize import metrics

ROOT = Path(__file__).resolve().parents[2]
COUNTRIES = ["Australia", "Bangladesh", "Brazil", "Egypt", "India", "Nepal", "United_States"]
TEST = list(range(2020, 2025))
LABEL = "REAL FIRMS DATA"


def decode(table: dict) -> pd.DataFrame:
    cols, dicts = table["columns"], table.get("dictionaries", {})
    rows = [[dicts[c][v] if c in dicts else v for c, v in zip(cols, r)] for r in table["rows"]]
    return pd.DataFrame(rows, columns=cols)


def national_daily(country: str) -> tuple[pd.DataFrame, dict]:
    data = json.loads((ROOT / "web/public/data" / f"{country}.json").read_text(encoding="utf-8"))
    daily = decode(data["daily_compact"]) if "daily_compact" in data else pd.DataFrame(data["daily"])
    daily["date"] = pd.to_datetime(daily["date"].astype(str).str[:10])
    for c in ["raw_terra", "raw_aqua", "raw_viirs", "raw", "harmonized", "lo", "hi"]:
        daily[c] = pd.to_numeric(daily[c], errors="coerce")
    return daily.set_index("date").sort_index(), data


def model_series(daily: pd.DataFrame, model_card: dict, country: str) -> pd.DataFrame:
    sel = model_card["selection"][country]["selected"]
    converted = daily["source"].astype(str).str.contains("converted VIIRS")
    out = pd.DataFrame({"Aqua": daily["raw_aqua"], "B0": daily["raw_viirs"],
                        "B1": daily["raw_viirs"] * model_card["ratios"]["B1"]}, index=daily.index)
    out[sel] = daily["harmonized"].where(converted)
    if "M1" not in out:
        out["M1"] = np.nan
    return out


def weekly_metrics(frame: pd.DataFrame, model: str) -> dict:
    sub = frame[["Aqua", model]].dropna()
    w = sub.resample("W-MON").sum(min_count=1).dropna()
    return {"n_weeks": int(len(w)), **metrics(w.Aqua, w[model])}


def a1_layer1(evaluation: pd.DataFrame, model_card: dict, out: Path) -> pd.DataFrame:
    rows = []
    for country in COUNTRIES:
        sel = model_card["selection"][country]
        for model in ["B0", "B1", "M1"]:
            r = evaluation[(evaluation.region == country) & (evaluation.model == model) &
                           (evaluation.split == "test") & (evaluation.aggregation == "weekly")].iloc[0]
            rows.append({"country": country, "model": model, "selected": model == sel["selected"],
                         "validation_daily_mae": sel["validation_daily_mae"].get(model),
                         "test_weeks": int(r.n_periods), "bias_pct": r.bias_pct, "mae": r.mae,
                         "correlation": r.correlation, "peak_week_error": r.peak_week_error})
    t = pd.DataFrame(rows)
    t.assign(label=LABEL).to_csv(out / "layer1_table.csv", index=False)
    lines = ["# Layer 1 results: held-out test years 2020-2024, weekly", "",
             f"Data: {LABEL}. Source: `reports/harmonization_eval.csv` (official locked evaluation, split=test, "
             "aggregation=weekly, pandas W-MON weeks), selection from `reports/harmonization_model.json`. "
             "Models were selected on 2018-2019 validation daily MAE before the test years were evaluated; "
             "B0 has no fitted parameter and was never a candidate. Units: Aqua-reference-equivalent detections "
             "per week; bias is (sum of model - sum of Aqua) / sum of Aqua over the test weeks.", "",
             "| Country | Model | Selected | Validation daily MAE | Test bias (%) | Test weekly MAE | Test weekly r |",
             "|---|---|---|---:|---:|---:|---:|"]
    for r in t.itertuples():
        v = "" if r.validation_daily_mae is None or pd.isna(r.validation_daily_mae) else f"{r.validation_daily_mae:,.2f}"
        lines.append(f"| {r.country.replace('_', ' ')} | {r.model} | {'**yes**' if r.selected else ''} | {v} | "
                     f"{r.bias_pct:+.1f} | {r.mae:,.1f} | {r.correlation:.3f} |")
    (out / "layer1_table.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return t


def a2_per_year(series: dict, model_card: dict, evaluation: pd.DataFrame, out: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    rows, check = [], []
    for country, frame in series.items():
        sel = model_card["selection"][country]["selected"]
        test = frame[frame.index.year.isin(TEST)]
        for model in ["B0", "B1", "M1"]:
            if frame[model].notna().sum() == 0:
                rows.append({"country": country, "year": "all", "model": model, "selected": model == sel,
                             "note": "not in published data (not the selected model)"})
                continue
            m = weekly_metrics(test, model)
            ref = evaluation[(evaluation.region == country) & (evaluation.model == model) &
                             (evaluation.split == "test") & (evaluation.aggregation == "weekly")].iloc[0]
            check.append({"country": country, "model": model, "mae_recomputed": m["mae"], "mae_official": ref.mae,
                          "bias_recomputed": m["bias_pct"], "bias_official": ref.bias_pct,
                          "r_recomputed": m["correlation"], "r_official": ref.correlation})
            for year in TEST:
                ym = weekly_metrics(frame[frame.index.year == year], model)
                rows.append({"country": country, "year": year, "model": model, "selected": model == sel, **ym})
    per_year, chk = pd.DataFrame(rows), pd.DataFrame(check)
    per_year.assign(label=LABEL).to_csv(out / "layer1_per_year.csv", index=False)
    chk.to_csv(out / "layer1_reproduction_check.csv", index=False)
    return per_year, chk


def a3_ratio(series: dict, daily: dict, out: Path) -> pd.DataFrame:
    rows = []
    for country, d in daily.items():
        both = d[(d.raw_aqua.notna()) & (d.raw_viirs.notna())]
        both = both[(both.index.year >= 2013) & (both.index.year <= 2024)]
        for year, g in both.groupby(both.index.year):
            rows.append({"country": country, "year": int(year), "days": int(len(g)),
                         "aqua": float(g.raw_aqua.sum()), "viirs": float(g.raw_viirs.sum()),
                         "viirs_per_aqua": float(g.raw_viirs.sum() / g.raw_aqua.sum()) if g.raw_aqua.sum() else np.nan})
    r = pd.DataFrame(rows)
    trend = []
    for country, g in r.groupby("country"):
        x, y = g.year.values, np.log(g.viirs_per_aqua.values)
        slope = np.polyfit(x, y, 1)[0]
        # year-block bootstrap of the log-linear slope (resample years with replacement)
        rng = np.random.default_rng(2024)
        boots = []
        for _ in range(2000):
            idx = rng.integers(0, len(x), len(x))
            if len(set(x[idx])) > 2:
                boots.append(np.polyfit(x[idx], y[idx], 1)[0])
        lo, hi = np.percentile(boots, [2.5, 97.5])
        train = g[g.year.between(2013, 2017)].viirs_per_aqua.mean()
        test = g[g.year.between(2020, 2024)].viirs_per_aqua.mean()
        trend.append({"country": country, "pct_per_year": 100 * (np.exp(slope) - 1),
                      "pct_per_year_ci_lo": 100 * (np.exp(lo) - 1), "pct_per_year_ci_hi": 100 * (np.exp(hi) - 1),
                      "mean_ratio_2013_2017": train, "mean_ratio_2020_2024": test,
                      "test_vs_train_pct": 100 * (test / train - 1)})
    r.assign(label=LABEL).to_csv(out / "ratio_by_year.csv", index=False)
    t = pd.DataFrame(trend)
    t.assign(label=LABEL).to_csv(out / "ratio_trend.csv", index=False)
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(9, 5))
    for country, g in r.groupby("country"):
        ax.plot(g.year, g.viirs_per_aqua, marker="o", label=country.replace("_", " "))
    ax.axvspan(2012.5, 2017.5, color="#e9ecef", zorder=0)
    ax.axvspan(2019.5, 2024.5, color="#fff3bf", zorder=0)
    ax.set_yscale("log")
    ax.set_xlabel("year")
    ax.set_ylabel("VIIRS detections per Aqua detection (log scale)")
    ax.set_title(f"[{LABEL}]  VIIRS-to-Aqua detection ratio by year (national, days with both archives)\n"
                 "grey = training years 2013-2017, yellow = held-out test years 2020-2024", fontsize=10)
    ax.legend(fontsize=8, ncol=2)
    fig.tight_layout()
    fig.savefig(out / "ratio_by_year.png", dpi=120)
    plt.close(fig)
    return t


def a4_overlap_plot(series: dict, out: Path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    paths = []
    for country in ["Nepal", "United_States"]:
        f = series[country]
        sel = [c for c in ["M1", "B1"] if f[c].notna().any() and c in ("M1", "B1")]
        model = "M1" if f["M1"].notna().any() else "B1"
        w = f[(f.index.year >= 2013) & (f.index.year <= 2024)][["Aqua", model, "B0"]].resample("W-MON").sum(min_count=1)
        fig, ax = plt.subplots(figsize=(12, 4.8))
        ax.plot(w.index, w.B0, color="#adb5bd", lw=0.8, label="raw VIIRS (B0)")
        ax.plot(w.index, w.Aqua, color="#1c7ed6", lw=1.1, label="observed MODIS Aqua")
        ax.plot(w.index, w[model], color="#e8590c", lw=1.0, alpha=0.9, label=f"VIIRS converted to Aqua scale ({model}, selected)")
        ax.set_yscale("symlog", linthresh=10)
        ax.axvspan(pd.Timestamp("2020-01-01"), pd.Timestamp("2024-12-31"), color="#fff3bf", zorder=0, label="held-out test years")
        ax.set_ylabel("detections per week (symlog)")
        ax.set_title(f"[{LABEL}]  {country.replace('_', ' ')}: observed Aqua vs converted VIIRS vs raw VIIRS, weekly 2013-2024",
                     fontsize=10)
        ax.legend(fontsize=8, loc="upper left", ncol=2)
        fig.tight_layout()
        path = out / f"aqua_vs_converted_viirs_{country}.png"
        fig.savefig(path, dpi=120)
        plt.close(fig)
        paths.append(path)
    return paths


def a5_distribution(series: dict, data: dict, out: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    rows = []
    for country, f in series.items():
        model = "M1" if f["M1"].notna().any() else "B1"
        w = f[(f.index.year >= 2013) & (f.index.year <= 2024)][["Aqua", model]].dropna().resample("W-MON").sum(min_count=1).dropna()
        for name, col in [("observed Aqua", "Aqua"), (f"converted VIIRS ({model})", model)]:
            v = w[col]
            rows.append({"country": country, "series": name, "weeks": int(len(v)),
                         "zero_week_share": float((v < 0.5).mean()), "p10": float(v.quantile(0.1)),
                         "p50": float(v.quantile(0.5)), "p90": float(v.quantile(0.9))})
    dist = pd.DataFrame(rows)
    dist.assign(label=LABEL).to_csv(out / "distribution_overlap.csv", index=False)
    flags = []
    for country, d in data.items():
        an = pd.DataFrame(d.get("anomalies", []))
        if an.empty:
            continue
        an["year"] = pd.to_datetime(an["date"].astype(str).str[:10]).dt.year
        an["kind"] = np.where(an["status"].astype(str).str.lower().str.contains("high|above"), "high", "low")
        for (year, kind), g in an.groupby(["year", "kind"]):
            flags.append({"country": country, "year": int(year), "kind": kind, "flags": int(len(g))})
    fl = pd.DataFrame(flags)
    fl.assign(label=LABEL).to_csv(out / "anomaly_flags_by_year.csv", index=False)
    return dist, fl


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", default="reports/review")
    a = ap.parse_args()
    out = ROOT / a.out
    out.mkdir(parents=True, exist_ok=True)
    evaluation = pd.read_csv(ROOT / "reports/harmonization_eval.csv")
    model_card = json.loads((ROOT / "reports/harmonization_model.json").read_text(encoding="utf-8"))
    daily, data, series = {}, {}, {}
    for c in COUNTRIES:
        daily[c], data[c] = national_daily(c)
        series[c] = model_series(daily[c], model_card, c)
    pd.set_option("display.width", 200)
    t1 = a1_layer1(evaluation, model_card, out)
    per_year, chk = a2_per_year(series, model_card, evaluation, out)
    print("A2 reproduction check (recomputed from published daily vs official weekly test metrics):")
    print(chk.round(4).to_string(index=False))
    trend = a3_ratio(series, daily, out)
    print("\nA3 ratio trend:\n" + trend.round(3).to_string(index=False))
    a4_overlap_plot(series, out)
    dist, flags = a5_distribution(series, data, out)
    print("\nA5 distribution:\n" + dist.round(3).to_string(index=False))
    if not flags.empty:
        flags["period"] = np.where(flags.year < 2013, "2003-2012 (observed Aqua)", "2013-2024 (converted VIIRS)")
        summary = flags.groupby(["country", "period", "kind"]).flags.sum().unstack("kind", fill_value=0)
        years = flags.groupby(["country", "period"]).year.nunique()
        print("\nA5 anomaly flags by period:\n" + summary.to_string())
        summary.to_csv(out / "anomaly_flags_by_period.csv")


if __name__ == "__main__":
    main()
