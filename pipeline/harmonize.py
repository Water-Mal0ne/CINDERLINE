"""Transparent ratio harmonization of archive detection counts, not true fire counts."""
from __future__ import annotations
import json
from pathlib import Path
import numpy as np
import pandas as pd

TRAIN = list(range(2013, 2018))
VALIDATION = [2018, 2019]
TEST = list(range(2020, 2025))
N_BOOT = 200
MAX_CELLS = 12
# First complete civil years after the instruments' partial opening years.
FIRST_COMPLETE_YEAR = {"Terra": 2001, "Aqua": 2003, "VIIRS": 2013}


def _strata(df):
    frp = pd.to_numeric(df.frp, errors="coerce")
    bins = np.select([frp < 10, frp < 50, frp >= 50], ["low", "medium", "high"], default="unknown")
    return df.daynight.fillna("?").astype(str) + ":" + bins


def fit_ratios(counts):
    """Fit B1 and partially pooled region/daynight/FRP ratios on training records only."""
    train = counts[counts.year.isin(TRAIN)]
    totals = train.groupby("stream").n.sum()
    if totals.get("VIIRS", 0) <= 0 or totals.get("Aqua", 0) <= 0:
        raise ValueError("Need Aqua and VIIRS detections in training years 2013–2017")
    global_ratio = float(totals["Aqua"] / totals["VIIRS"])
    table = train.groupby(["country", "stratum", "stream"]).n.sum().unstack("stream", fill_value=0)
    ratios = {}
    for (country, stratum), row in table.iterrows():
        viirs, aqua = float(row.get("VIIRS", 0)), float(row.get("Aqua", 0))
        # Shrink sparse strata toward B1 with 100 VIIRS-equivalent observations.
        ratios[f"{country}|{stratum}"] = (aqua + 100 * global_ratio) / (viirs + 100)
    return {"B1": global_ratio, "M1": ratios}


def predict_counts(frame, model, ratios):
    if model == "B0":
        return frame.n.to_numpy(float)
    if model == "B1":
        return frame.n.to_numpy(float) * ratios["B1"]
    weights = [ratios["M1"].get(f"{c}|{s}", ratios["B1"]) for c, s in zip(frame.country, frame.stratum)]
    return frame.n.to_numpy(float) * np.asarray(weights)


def _archive_years(df, country, stream):
    manifest = df.attrs.get("manifest", {})
    sensor = "viirs-snpp" if stream == "VIIRS" else "modis"
    files = manifest.get("files", [])
    archive_years = {int(r["year"]) for r in files if r.get("country") == country and r.get("sensor") == sensor
                     and r.get("complete") and r.get("status") in ("complete", "ok")}
    # Include only local years bracketed by adjacent annual UTC archives.
    if archive_years:
        return {y for y in archive_years if y - 1 in archive_years and y + 1 in archive_years
                and y >= FIRST_COMPLETE_YEAR[stream]}
    return set()  # absence of a manifest does not establish zero-detection days


def metrics(reference, estimate):
    a, b = np.asarray(reference, float), np.asarray(estimate, float)
    finite = np.isfinite(a) & np.isfinite(b)
    a, b = a[finite], b[finite]
    if not len(a):
        return dict(bias_pct=None, mae=None, correlation=None)
    return dict(bias_pct=float(100 * (b.sum() - a.sum()) / a.sum()) if a.sum() else None,
                mae=float(np.mean(np.abs(b - a))),
                correlation=float(np.corrcoef(a, b)[0, 1]) if len(a) > 1 and np.std(a) and np.std(b) else None)


def _evaluate(daily, region, model, split, years):
    subset = daily[daily.index.year.isin(years)][["Aqua", model]].dropna()
    rows = []
    for aggregation, frequency in [("monthly", "MS"), ("weekly", "W-MON")]:
        grouped = subset.resample(frequency).sum(min_count=1).dropna()
        peak_errors = []
        for _, year_data in subset.groupby(subset.index.year):
            weekly = year_data.resample("W-MON").sum(min_count=1).dropna()
            if len(weekly) and weekly.Aqua.sum() > 0 and weekly[model].sum() > 0:
                peak_errors.append(abs((weekly.Aqua.idxmax() - weekly[model].idxmax()).days) / 7)
        rows.append(dict(region=region, model=model, split=split, aggregation=aggregation,
                         n_periods=int(len(grouped)), **metrics(grouped.Aqua, grouped[model]),
                         peak_week_error=float(np.mean(peak_errors)) if peak_errors else None))
    return rows


def _daily(counts, country, cell, date_index, ratios, availability):
    selected = counts[(counts.country == country) & (counts.cell_id == cell)]
    table = selected.groupby(["date", "stream"]).n.sum().unstack("stream") if len(selected) else pd.DataFrame()
    table = table.reindex(date_index)
    for stream in ["Terra", "Aqua", "VIIRS"]:
        values = table.get(stream, pd.Series(np.nan, index=date_index))
        # Zero denotes no archived qualifying detections; never asserts a cloud-free no-fire observation.
        available = date_index.year.isin(availability[stream])
        table[stream] = values.where(~available, values.fillna(0)).where(available)
    v = selected[selected.stream == "VIIRS"].copy()
    for model in ["B0", "B1", "M1"]:
        if len(v):
            v["pred"] = predict_counts(v, model, ratios)
            estimates = v.groupby("date").pred.sum().reindex(date_index)
        else:
            estimates = pd.Series(np.nan, index=date_index)
        table[model] = estimates.fillna(0).where(date_index.year.isin(availability["VIIRS"]))
    return table


def bootstrap_daily(cell_counts, date_index, country, model, bootstrap):
    """Exact linear ratio predictions with one pivot and a matrix product per map cell."""
    if not len(cell_counts):
        return np.zeros((len(bootstrap), len(date_index)))
    design = cell_counts.pivot_table(index="date", columns="stratum", values="n", aggfunc="sum", fill_value=0,
                                    observed=True).reindex(date_index, fill_value=0)
    strata = list(design.columns)
    if model == "B1":
        weights = np.array([[fit["B1"]] * len(strata) for fit in bootstrap])
    else:
        weights = np.array([[fit["M1"].get(f"{country}|{s}", fit["B1"]) for s in strata] for fit in bootstrap])
    return (design.to_numpy(float) @ weights.T).T


def raw_display_series(daily):
    """Construct the display baseline from eligible archives, not a hardcoded switch date.

    Eligibility is already applied by _daily. This function does not change B0/B1/M1
    predictions or their held-out evaluation. No Terra/Aqua pooling is performed.
    """
    return daily.VIIRS.where(daily.VIIRS.notna(), daily.Aqua)


def run(detections, output_dir):
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    label = detections.attrs.get("label", "UNVERIFIED INPUT")
    main = detections[detections.type == 0].copy()
    main["date"] = pd.to_datetime(main.local_date).dt.normalize()
    main["stratum"] = _strata(main)
    # Aggregate before calibration, preserving cell, country, instrument and experimental strata.
    counts = main.groupby(["country", "cell_id", "date", "year", "stratum", "stream"], observed=True).size().rename("n").reset_index()
    country_counts = counts.groupby(["country", "date", "year", "stratum", "stream"], observed=True).n.sum().reset_index()
    country_counts["cell_id"] = "ALL"
    counts = pd.concat([counts, country_counts], ignore_index=True)
    fit_input = country_counts.copy()
    # Only train on years for which both annual archives plus local-date edges are available.
    common_years = {c: _archive_years(detections, c, "Aqua") & _archive_years(detections, c, "VIIRS") for c in main.country.unique()}
    fit_input = fit_input[[int(y) in common_years[c] for c, y in zip(fit_input.country, fit_input.year)]]
    ratios = fit_ratios(fit_input)
    bootstrap = []
    rng = np.random.default_rng(2841)
    years = sorted(set(fit_input[fit_input.year.isin(TRAIN)].year))
    for _ in range(N_BOOT):
        sampled = rng.choice(years, size=len(years), replace=True)
        resampled = pd.concat([fit_input[fit_input.year == y] for y in sampled], ignore_index=True)
        bootstrap.append(fit_ratios(resampled))
    rows, eval_rows, selections, history = [], [], {}, {}
    for country in sorted(main.country.unique()):
        availability = {s: _archive_years(detections, country, s) for s in ["Terra", "Aqua", "VIIRS"]}
        viable = availability["Aqua"] | availability["VIIRS"]
        if not viable:
            continue
        date_index = pd.date_range(f"{min(viable)}-01-01", f"{max(viable)}-12-31", name="date")
        history[country] = {"start": str(date_index[0].date()), "end": str(date_index[-1].date()),
                            "first_eligible_viirs_year": min(availability["VIIRS"]) if availability["VIIRS"] else None,
                            "early_source": "Observed MODIS Aqua; no Terra reconstruction"}
        whole = _daily(counts, country, "ALL", date_index, ratios, availability)
        validation = {model: metrics(whole.loc[whole.index.year.isin(VALIDATION), "Aqua"],
                                     whole.loc[whole.index.year.isin(VALIDATION), model])["mae"] for model in ["B1", "M1"]}
        selected_model = "M1" if validation["M1"] is not None and validation["B1"] is not None and validation["M1"] < validation["B1"] else "B1"
        selections[country] = {"selected": selected_model, "validation_daily_mae": validation}
        for model in ["B0", "B1", "M1"]:
            eval_rows.extend(_evaluate(whole, country, model, "validation", VALIDATION))
            eval_rows.extend(_evaluate(whole, country, model, "test", TEST))
        train_cells = main[(main.country == country) & main.year.isin(TRAIN)].groupby("cell_id").size().nlargest(MAX_CELLS).index.tolist()
        for cell in ["ALL", *train_cells]:
            daily = whole if cell == "ALL" else _daily(counts, country, cell, date_index, ratios, availability)
            cell_counts = counts[(counts.country == country) & (counts.cell_id == cell) & (counts.stream == "VIIRS")].copy()
            boot_daily = bootstrap_daily(cell_counts, date_index, country, selected_model, bootstrap)
            lo, hi = np.percentile(boot_daily, [2.5, 97.5], axis=0)
            prediction = daily[selected_model].to_numpy()
            source = np.where(np.isfinite(prediction), "converted VIIRS", np.where(daily.Aqua.notna(), "observed Aqua", "unavailable"))
            result = np.where(np.isfinite(prediction), prediction, daily.Aqua)
            raw = raw_display_series(daily)
            lo = np.where(np.isfinite(prediction), lo, daily.Aqua)
            hi = np.where(np.isfinite(prediction), hi, daily.Aqua)
            for i, date in enumerate(date_index):
                streams = [s for s in ["Terra", "Aqua", "VIIRS"] if date.year in availability[s]]
                rows.append(dict(date=date.strftime("%Y-%m-%d"), region=country, cell_id=cell,
                                 raw_terra=daily.Terra.iloc[i], raw_aqua=daily.Aqua.iloc[i], raw_viirs=daily.VIIRS.iloc[i],
                                 raw=raw.iloc[i],
                                 harmonized=float(result[i]), lo=float(lo[i]), hi=float(hi[i]),
                                 coverage="archive: " + ",".join(streams) + "; observation coverage unknown",
                                 source=source[i], model=selected_model if source[i] == "converted VIIRS" else "Aqua reference",
                                 label=label))
    harmonized, evaluation = pd.DataFrame(rows), pd.DataFrame(eval_rows)
    harmonized.attrs.update(label=label, manifest=detections.attrs.get("manifest", {}), model_selection=selections)
    evaluation["label"] = label
    evaluation.to_csv(output / "harmonization_eval.csv", index=False)
    model_card = {"label": label, "fit_years": TRAIN, "validation_years": VALIDATION, "test_years": TEST,
                  "ratios": ratios, "selection": selections, "history": history, "grid_size": 0.25, "map_cells": MAX_CELLS,
                  "uncertainty": "95% training-year bootstrap calibration interval; not total observation/prediction uncertainty",
                  "limitations": ["Counts refer to archived qualifying detections, not fires or burned area.",
                                  "Cloud/overpass observation coverage is unknown; zeros mean no archived detections only.",
                                  "Full local years require adjacent UTC annual archives.",
                                  "No validated pre-Aqua bridge; this build supports dates with Aqua or VIIRS archives.",
                                  "Early observed-Aqua bounds equal the archived count because no conversion is applied; observation uncertainty remains unknown.",
                                  "M1 matches reported FRP strata empirically, not physically equal pixel-scale energy.",
                                  "M2 omitted; map exposes 12 training-period-active cells per country, national totals use all cells."]}
    (output / "harmonization_model.json").write_text(json.dumps(model_card, indent=2), encoding="utf-8")
    test_rows = evaluation[(evaluation.split == "test") & (evaluation.aggregation == "monthly")]
    summary = ["# Harmonization evaluation", "", f"Data: **{label}**", "", "Model selected on 2018–2019 daily MAE; final metrics on 2020–2024.", "", "```csv", test_rows.to_csv(index=False), "```", "", *[f"- {x}" for x in model_card["limitations"]]]
    (output / "harmonization_summary.md").write_text("\n".join(summary), encoding="utf-8")
    return harmonized, evaluation
