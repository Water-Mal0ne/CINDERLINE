"""Grid sensitivity and an early Terra/Aqua bridge feasibility check.

This command never selects a released model or evaluates the 2020–2024 test set.
It reads verified sufficient counts, writes a prespecified protocol first, and
produces independent validation reports. It does not publish a reconstruction.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import time

import numpy as np
import pandas as pd

from pipeline import harmonize
from pipeline.globe import manifest_fingerprint
from pipeline.streaming.aggregate_archives import peak_rss_bytes, write_json
from pipeline.streaming.prepare_analysis import input_snapshot
from pipeline.streaming.prepared_runtime import read_inputs

GRID_TRAIN = tuple(range(2013, 2018))
GRID_VALIDATION = (2018, 2019)
BRIDGE_TRAIN = tuple(range(2003, 2008))
BRIDGE_VALIDATION = tuple(range(2008, 2012))
BOOTSTRAPS = 200


def coarse_cell(cell: str) -> str:
    """Parent 0.5-degree origin, including negative coordinate boundaries."""
    lat, lon = map(float, cell.split(":"))
    ticks = [round(v * 4) for v in (lat, lon)]
    if any(abs(v * 4 - tick) > 1e-7 for v, tick in zip((lat, lon), ticks)):
        raise ValueError("Expected a 0.25-degree grid origin")
    return f"{(ticks[0] // 2) / 2:.2f}:{(ticks[1] // 2) / 2:.2f}"


def children(cell: str) -> list[str]:
    lat, lon = map(float, cell.split(":"))
    return [f"{lat + dy:.2f}:{lon + dx:.2f}" for dy in (0, .25) for dx in (0, .25)]


def select_training_cells(frame: pd.DataFrame, limit: int = 12) -> list[str]:
    train = frame[frame.year.isin(GRID_TRAIN)].copy()
    train["coarse_cell"] = train.cell_id.map(coarse_cell)
    rank = train.groupby("coarse_cell", observed=True).n.sum().rename("n").reset_index()
    return rank.sort_values(["n", "coarse_cell"], ascending=[False, True]).head(limit).coarse_cell.tolist()


def paired_daily(frame, country, model, ratios, cells, years):
    dates = pd.date_range(f"{min(years)}-01-01", f"{max(years)}-12-31")
    index = pd.MultiIndex.from_product([cells, dates], names=["cell_id", "date"])
    aqua = frame[frame.stream == "Aqua"].groupby(["cell_id", "date"], observed=True).n.sum()
    viirs = frame[frame.stream == "VIIRS"].copy()
    viirs["prediction"] = harmonize.predict_counts(viirs, model, ratios)
    predicted = viirs.groupby(["cell_id", "date"], observed=True).prediction.sum()
    return pd.DataFrame({"Aqua": aqua.reindex(index, fill_value=0),
                         "estimate": predicted.reindex(index, fill_value=0)})


def spatial_metrics(paired):
    daily = paired.reset_index()
    daily["month"] = daily.date.dt.to_period("M").astype(str)
    daily["year"] = daily.date.dt.year
    daily["week"] = (daily.date.dt.dayofyear - 1) // 7 + 1
    monthly = daily.groupby(["cell_id", "month"], observed=True)[["Aqua", "estimate"]].sum()
    total = float(monthly.Aqua.sum())
    union = int(((daily.Aqua > 0) | (daily.estimate > 0)).sum())
    overlap = int(((daily.Aqua > 0) & (daily.estimate > 0)).sum())
    weekly = daily.groupby(["cell_id", "year", "week"], observed=True)[["Aqua", "estimate"]].sum()
    peak_errors = []
    for _, group in weekly.groupby(level=["cell_id", "year"]):
        if group.Aqua.sum() > 0 and group.estimate.sum() > 0:
            peak_errors.append(abs(int(group.Aqua.idxmax()[2]) - int(group.estimate.idxmax()[2])))
    return {
        "cells": int(daily.cell_id.nunique()), "cell_days": int(len(daily)),
        "aqua_detections": total, "converted_detections": float(monthly.estimate.sum()),
        "monthly_mae_per_cell": float((monthly.estimate - monthly.Aqua).abs().mean()),
        "monthly_normalized_absolute_error_pct": float(100 * (monthly.estimate - monthly.Aqua).abs().sum() / total) if total else None,
        "bias_pct": float(100 * (monthly.estimate.sum() - total) / total) if total else None,
        "recorded_activity_jaccard": overlap / union if union else None,
        "active_union_cell_days": union, "mean_peak_week_error": float(np.mean(peak_errors)) if peak_errors else None,
        "peak_cell_years": len(peak_errors),
    }


def grid_check(partitions, daily_paths, model, output):
    selected, invariant = {}, []
    for country, path in daily_paths.items():
        annuals = [pd.read_parquet(path.parent / f"annual_{country}_{year}.parquet")
                   for year in (*GRID_TRAIN, *GRID_VALIDATION)]
        annual = pd.concat(annuals, ignore_index=True)
        selected[country] = select_training_cells(annual)
        choice = model["selection"][country]["selected"]
        for year, rows in annual[annual.stream == "VIIRS"].groupby("year", observed=True):
            fine = float(harmonize.predict_counts(rows, choice, model["ratios"]).sum())
            coarse = rows.copy()
            coarse["cell_id"] = coarse.cell_id.map(coarse_cell)
            coarse = coarse.groupby(["country", "cell_id", "stratum"], observed=True).n.sum().reset_index()
            merged = float(harmonize.predict_counts(coarse, choice, model["ratios"]).sum())
            np.testing.assert_allclose(fine, merged, atol=1e-7, rtol=1e-12)
            invariant.append({"country": country, "year": int(year), "fine": fine, "coarse": merged, "difference": merged - fine})
    write_json(output / "grid_selection_lock.json", {"selection_years": GRID_TRAIN, "selected_coarse_cells": selected})
    reduced = []
    columns = ["country", "cell_id", "local_date", "year", "stratum", "stream", "type", "n"]
    for i, path in enumerate(partitions):
        frame = pd.read_parquet(path, columns=columns)
        frame = frame[(frame.type == 0) & frame.year.isin(GRID_VALIDATION) & frame.stream.isin(["Aqua", "VIIRS"])].copy()
        if not frame.empty:
            frame["parent"] = frame.cell_id.map(coarse_cell)
            frame = frame[[parent in selected[country] for parent, country in zip(frame.parent, frame.country)]]
            if not frame.empty:
                frame["date"] = pd.to_datetime(frame.local_date).dt.normalize()
                reduced.append(frame.groupby(["country", "cell_id", "date", "stratum", "stream"], observed=True).n.sum().reset_index())
        if (i + 1) % 100 == 0:
            print(f"Sensitivity reduction: {i + 1}/{len(partitions)} partitions", flush=True)
    counts = pd.concat(reduced, ignore_index=True).groupby(["country", "cell_id", "date", "stratum", "stream"], observed=True).n.sum().reset_index()
    rows = []
    for country in sorted(selected):
        fine_counts = counts[counts.country == country].copy()
        coarse_counts = fine_counts.copy()
        coarse_counts["cell_id"] = coarse_counts.cell_id.map(coarse_cell)
        coarse_counts = coarse_counts.groupby(["country", "cell_id", "date", "stratum", "stream"], observed=True).n.sum().reset_index()
        fine_ids = [child for parent in selected[country] for child in children(parent)]
        model_name = model["selection"][country]["selected"]
        fine = paired_daily(fine_counts, country, model_name, model["ratios"], fine_ids, GRID_VALIDATION)
        coarse = paired_daily(coarse_counts, country, model_name, model["ratios"], selected[country], GRID_VALIDATION)
        np.testing.assert_allclose(fine.sum(), coarse.sum(), atol=1e-8, rtol=1e-12)
        for size, paired in [(.25, fine), (.5, coarse)]:
            rows.append({"country": country, "grid_degrees": size, "model": model_name, **spatial_metrics(paired)})
    pd.DataFrame(rows).to_csv(output / "grid_sensitivity.csv", index=False)
    write_json(output / "grid_invariance.json", {"years": [*GRID_TRAIN, *GRID_VALIDATION],
        "checks": invariant, "max_absolute_difference": max(abs(r["difference"]) for r in invariant),
        "meaning": "National invariance follows from linear country/stratum conversion, not evidence of spatial robustness."})
    return rows


def bridge_ratio(annual):
    train = annual.loc[list(BRIDGE_TRAIN)]
    denominator = float(train.Terra.sum())
    if denominator <= 0:
        raise ValueError("No Terra training support")
    return float(train.Aqua.sum() / denominator)


def bridge_check(daily_paths, output):
    rows, parameters, intervals = [], {}, []
    for country, path in sorted(daily_paths.items()):
        frame = pd.read_parquet(path)
        frame = frame[(frame.cell_id == "ALL") & frame.year.isin((*BRIDGE_TRAIN, *BRIDGE_VALIDATION)) & frame.stream.isin(["Terra", "Aqua"])]
        dates = pd.date_range("2003-01-01", "2011-12-31")
        paired = frame.groupby(["date", "stream"], observed=True).n.sum().unstack("stream").reindex(dates, fill_value=0).fillna(0)
        annual = paired.groupby(paired.index.year).sum()
        ratio = bridge_ratio(annual)
        train = annual.loc[list(BRIDGE_TRAIN)]
        rng = np.random.default_rng(7318)
        indices = rng.integers(0, len(train), size=(BOOTSTRAPS, len(train)))
        draws = train.Aqua.to_numpy()[indices].sum(axis=1) / train.Terra.to_numpy()[indices].sum(axis=1)
        lo, hi = np.percentile(draws, [2.5, 97.5])
        parameters[country] = {"ratio": ratio, "ratio_95pct_training_year_bootstrap": [float(lo), float(hi)],
            "training_years": BRIDGE_TRAIN, "validation_years": BRIDGE_VALIDATION, "bootstrap_draws": BOOTSTRAPS,
            "annual_observed_ratios": {str(y): float(r.Aqua/r.Terra) if r.Terra else None for y,r in annual.iterrows()}}
        validation = paired[paired.index.year.isin(BRIDGE_VALIDATION)].copy()
        validation["unscaled_Terra"] = validation.Terra
        validation["training_ratio"] = validation.Terra * ratio
        for model_name in ["unscaled_Terra", "training_ratio"]:
            for aggregate in ["monthly", "weekly"]:
                table = validation[["Aqua", model_name]].copy()
                if aggregate == "monthly":
                    grouped = table.groupby([table.index.year, table.index.month]).sum()
                else:
                    grouped = table.groupby([table.index.year, (table.index.dayofyear - 1) // 7 + 1]).sum()
                peak_errors = []
                for year, year_data in validation.groupby(validation.index.year):
                    weekly = year_data.groupby((year_data.index.dayofyear - 1) // 7 + 1)[["Aqua", model_name]].sum()
                    if weekly.Aqua.sum() > 0 and weekly[model_name].sum() > 0:
                        peak_errors.append(abs(int(weekly.Aqua.idxmax()) - int(weekly[model_name].idxmax())))
                rows.append({"country": country, "model": model_name, "aggregation": aggregate,
                    "n_periods": len(grouped), **harmonize.metrics(grouped.Aqua, grouped[model_name]),
                    "mean_peak_week_error": float(np.mean(peak_errors)) if peak_errors else None})
        monthly = validation.groupby([validation.index.year, validation.index.month]).sum()
        included = (monthly.Aqua >= monthly.Terra * lo) & (monthly.Aqua <= monthly.Terra * hi)
        active = (monthly.Aqua > 0) | (monthly.Terra > 0)
        intervals.append({"country": country, "active_months": int(active.sum()),
            "reference_inside_calibration_interval_pct": float(100*included[active].mean()),
            "interpretation": "Descriptive reference inclusion only. Calibration intervals are not predictive or total-uncertainty intervals."})
    pd.DataFrame(rows).to_csv(output / "terra_bridge_validation.csv", index=False)
    write_json(output / "terra_bridge_parameters.json", {"parameters": parameters, "interval_diagnostics": intervals,
        "reconstruction_published": False, "qualification": "Feasibility validation only; no early reconstruction or total-uncertainty claim."})
    return rows, parameters, intervals


def write_report(output, grid, bridge, parameters, intervals, fingerprint):
    grid_rows, bridge_rows = pd.DataFrame(grid), pd.DataFrame(bridge)
    lines = ["# Additional scientific validation", "", "These checks do not change the seven-country model, the 2020–2024 test evaluation, or the supported 2003–2024 product history.", "",
        "## Prespecified design", "", "The protocol was saved before calculation. Grid sensitivity freezes the released ratios and country choices, selects 12 coarse cells per country from 2013–2017 vegetation activity, and compares those cells with their four 0.25° children on 2018–2019. Both grids cover exactly the same selected geography; this is a selected-cell sensitivity check, not a claim for every cell.", "",
        "This grid diagnostic reuses the 2018–2019 block that originally selected each country model. It is not an independent confirmation or a new untouched test. Training activity sums vegetation detections across the separate streams; the selected 0.5° footprints and their four children are clipped to records in each country archive.", "",
        "The bridge fits one Terra-to-Aqua ratio per country from 2003–2007 and validates on the separate 2008–2011 year block. The unscaled Terra baseline is reported too. The 200 resamples draw entire training years. No candidate or acceptance threshold was chosen after observing validation, and no 2020–2024 data enter either new check.", "",
        "## Grid sensitivity", "", "| Country | 0.25° normalized monthly absolute error | 0.5° normalized monthly absolute error | 0.25° activity Jaccard | 0.5° activity Jaccard |", "| --- | ---: | ---: | ---: | ---: |"]
    for country in sorted(grid_rows.country.unique()):
        fine = grid_rows[(grid_rows.country == country)&(grid_rows.grid_degrees == .25)].iloc[0]
        coarse = grid_rows[(grid_rows.country == country)&(grid_rows.grid_degrees == .5)].iloc[0]
        lines.append(f"| {country.replace('_',' ')} | {fine.monthly_normalized_absolute_error_pct:.2f}% | {coarse.monthly_normalized_absolute_error_pct:.2f}% | {fine.recorded_activity_jaccard:.3f} | {coarse.recorded_activity_jaccard:.3f} |")
    lines += ["", "Normalized absolute error sums absolute cell-month error over observed Aqua counts across the same geography. Coarsening can cancel local positive/negative errors and merge different within-cell detections; lower error or higher recorded-activity Jaccard is therefore partly an aggregation effect. It does not establish more accurate fire locations, independent truth, or spatial robustness. The full CSV also reports bias, raw per-cell MAE and peak timing. Grid choice remains 0.25°; it was not retuned from these results.", "",
        "National totals were invariant for every country and each 2013–2019 year up to floating-point summation noise. That is expected because the conversion weights depend on country and sensor strata, not cell identity. It is an arithmetic property, not an independent validation result.", "",
        "## Early Terra bridge feasibility", "", "| Country | Training Aqua/Terra ratio | Unscaled monthly MAE | Converted monthly MAE | Converted validation bias | Mean peak-week error |", "| --- | ---: | ---: | ---: | ---: | ---: |"]
    for country in sorted(parameters):
        original = bridge_rows[(bridge_rows.country==country)&(bridge_rows.model=='unscaled_Terra')&(bridge_rows.aggregation=='monthly')].iloc[0]
        converted = bridge_rows[(bridge_rows.country==country)&(bridge_rows.model=='training_ratio')&(bridge_rows.aggregation=='monthly')].iloc[0]
        lines.append(f"| {country.replace('_',' ')} | {parameters[country]['ratio']:.4f} | {original.mae:.2f} | {converted.mae:.2f} | {converted.bias_pct:+.2f}% | {converted.mean_peak_week_error:.2f} |")
    lines += ["", "A positive constant ratio cannot change Terra's peak timing. Differences in overpass time and unmeasured observation conditions remain; a lower count error is not evidence that the instruments observed identical fires. Whole-year bootstrap bounds describe uncertainty in the fitted ratio, not the additional uncertainty of historical reconstruction.", "", "Observed Aqua lay inside the ratio-only 95% calibration interval in the following fractions of active validation months: " + "; ".join(f"{r['country'].replace('_',' ')} {r['reference_inside_calibration_interval_pct']:.1f}%" for r in intervals) + ". These are descriptive inclusion rates, not confidence-interval coverage guarantees.", "",
        "No 2001–2002 reconstruction is published. This feasibility test documents whether a simple bridge improves count agreement; it does not qualify wider total-uncertainty bands or validate transfer to the pre-Aqua period. The supported record remains 2003–2024. A future bridge needs an explicit reconstruction/uncertainty validation protocol before release.", "", "## Reproduction and scope", "", f"Archive manifest fingerprint: `{fingerprint}`. `protocol.json` binds the saved model SHA256 and experimental years. Raw observations are never expanded from counts. Archive-complete zero means no qualifying archived detections, not known cloud-free absence of fire; satellite observation coverage is unknown.", "", "Run `python -m pipeline.validation.science_checks --help` for the three preparation paths, three analysis paths, locked model and fresh output directory. The original model and lock are read-only. All output is separate from production model/evaluation files."]
    (output / "SCIENTIFIC_SENSITIVITY.md").write_text("\n".join(lines)+"\n",encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--preparations", nargs="+", required=True)
    parser.add_argument("--analyses", nargs="+", required=True)
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("Use a fresh output directory; prior validation is preserved.")
    manifest, partitions = input_snapshot(args.preparations)
    analysis_manifest, paths, _ = read_inputs(args.analyses)
    model = json.loads(args.model.read_text())
    fingerprint = manifest_fingerprint(manifest)
    if fingerprint != manifest_fingerprint(analysis_manifest) or fingerprint != model["archive_manifest_fingerprint"]:
        raise ValueError("Preparation, analysis and model sources differ")
    carrier = pd.DataFrame()
    carrier.attrs["manifest"] = manifest
    for country in paths:
        for stream, years in [("Aqua", (*BRIDGE_TRAIN,*BRIDGE_VALIDATION,*GRID_TRAIN,*GRID_VALIDATION)),
                              ("Terra", (*BRIDGE_TRAIN,*BRIDGE_VALIDATION)), ("VIIRS", (*GRID_TRAIN,*GRID_VALIDATION))]:
            if not set(years).issubset(harmonize._archive_years(carrier,country,stream)):
                raise ValueError(f"Required complete archives missing: {country}/{stream}")
    args.output.mkdir(parents=True)
    protocol = {"archive_manifest_fingerprint":fingerprint,"model_sha256":hashlib.sha256(args.model.read_bytes()).hexdigest(),
        "script_sha256":hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "grid_selection_years":GRID_TRAIN,"grid_validation_years":GRID_VALIDATION,"grid_coarse_cells_per_country":12,
        "grid_models":"Frozen released country choice and training ratios; no refit or model selection",
        "bridge_training_years":BRIDGE_TRAIN,"bridge_validation_years":BRIDGE_VALIDATION,
        "bridge_models":["unscaled Terra", "one per-country training-total Aqua/Terra ratio"],"bootstrap_draws":BOOTSTRAPS,
        "test_2020_2024_evaluated":False,"reconstruction_published":False,
        "publication_effect":"None; validation reports only"}
    write_json(args.output/"protocol.json",protocol)
    start = time.monotonic()
    grid = grid_check(partitions,paths,model,args.output)
    bridge,parameters,intervals = bridge_check(paths,args.output)
    write_report(args.output,grid,bridge,parameters,intervals,fingerprint)
    write_json(args.output/"RUN.json",{"status":"completed","seconds":round(time.monotonic()-start,2),
        "peak_rss_bytes":peak_rss_bytes(),"grid_metric_rows":len(grid),"bridge_metric_rows":len(bridge),
        "model_unchanged":hashlib.sha256(args.model.read_bytes()).hexdigest()==protocol["model_sha256"]})
    print(json.dumps({"output":str(args.output),"countries":len(paths),"seconds":round(time.monotonic()-start,2)},indent=2))


if __name__ == "__main__":
    main()
