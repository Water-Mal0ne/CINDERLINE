"""Reproduce the existing unmasked India/Nepal whole-year season example.

From the repository root:
    python scripts/verify_season_example.py --check

Use --write to generate the review CSV and source receipt. Optional
--reference-summary PATH compares every column with the original experiment's
whole_year_comparison.csv. No model fitting, outage masking or download occurs.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

COUNTRIES = ("India", "Nepal")
YEARS = tuple(range(2020, 2025))
INPUTS = (
    "data/sample/seven_country_national_counts.parquet",
    "reports/harmonization_model.json",
    "reports/selection_lock.json",
)
DESTINATION = "reports/review/season/original_whole_year_comparison.csv"
RECEIPT = "reports/review/season/original_whole_year_inputs.json"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def metrics(reference: np.ndarray, candidate: np.ndarray, dates: pd.DatetimeIndex) -> dict:
    require(bool(np.isfinite(reference).all() and np.isfinite(candidate).all()), "Nonfinite counts")
    require(bool((reference >= 0).all() and (candidate >= 0).all()), "Negative counts")
    ref = np.array([reference[dates.month == m].sum() for m in range(1, 13)], dtype=float)
    alt = np.array([candidate[dates.month == m].sum() for m in range(1, 13)], dtype=float)
    require(bool(ref.sum() > 0 and alt.sum() > 0), "Undefined zero-total comparison")
    ref_peaks = set(np.flatnonzero(np.abs(ref - ref.max()) <= 1e-12))
    alt_peaks = set(np.flatnonzero(np.abs(alt - alt.max()) <= 1e-12))
    return {
        "tv": float(0.5 * np.abs(ref / ref.sum() - alt / alt.sum()).sum()),
        "abs_annual_error": float(abs(alt.sum() - ref.sum()) / ref.sum()),
        "monthly_mae": float(np.abs(ref - alt).mean()),
        "peak_agreement": int(bool(ref_peaks & alt_peaks)),
    }


def compare(actual: pd.DataFrame, expected: pd.DataFrame) -> None:
    keys = ["country", "alternative"]
    expected = expected[expected.country.isin(COUNTRIES)].sort_values(keys).reset_index(drop=True)
    actual = actual.sort_values(keys).reset_index(drop=True)
    require(list(actual.columns) == list(expected.columns), "Comparison columns differ")
    require(actual[keys].equals(expected[keys]), "Comparison countries/models differ")
    for column in actual.columns.difference(keys):
        require(bool(np.allclose(actual[column], expected[column], rtol=1e-12, atol=1e-12)),
                f"Saved comparison differs: {column}")


def reproduce(repo: Path) -> tuple[pd.DataFrame, dict]:
    model = json.loads((repo / INPUTS[1]).read_text(encoding="utf-8"))
    selection = json.loads((repo / INPUTS[2]).read_text(encoding="utf-8"))
    require(model["ratios"] == selection["ratios"], "Frozen ratios disagree")
    require(model["selection"] == selection["selection"], "Frozen selections disagree")
    require(model["archive_manifest_fingerprint"] == selection["archive_manifest_fingerprint"],
            "Model and selection source fingerprints differ")
    counts = pd.read_parquet(repo / INPUTS[0])
    require(counts.attrs.get("archive_manifest_fingerprint") == model["archive_manifest_fingerprint"],
            "Count and model source fingerprints differ")
    require(counts.attrs.get("label") == "REAL FIRMS DATA", "Input is not labeled real FIRMS data")
    counts["date"] = pd.to_datetime(counts.date)
    require(bool(counts.year.eq(counts.date.dt.year).all()), "Count years disagree with dates")
    require(bool(counts.cell_id.eq("ALL").all()), "Expected national sufficient statistics")
    require(bool(np.isfinite(counts.n).all() and counts.n.ge(0).all()
                 and np.equal(counts.n, np.floor(counts.n)).all()), "Invalid detection multiplicities")
    ratio = float(model["ratios"]["B1"])
    require(bool(np.isfinite(ratio) and ratio > 0), "Invalid B1 ratio")
    annual = []
    for country in COUNTRIES:
        chosen = model["selection"][country]["selected"]
        require(chosen in {"B1", "M1"}, "Unsupported selected model")
        for year in YEARS:
            dates = pd.date_range(f"{year}-01-01", f"{year}-12-31")
            subset = counts[counts.country.eq(country) & counts.year.eq(year)]
            aqua = subset[subset.stream.eq("Aqua")]
            viirs = subset[subset.stream.eq("VIIRS")].copy()
            reference = aqua.groupby("date").n.sum().reindex(dates, fill_value=0).to_numpy(float)
            raw = viirs.groupby("date").n.sum().reindex(dates, fill_value=0).to_numpy(float)
            weights = [ratio if chosen == "B1" else float(model["ratios"]["M1"].get(
                f"{country}|{stratum}", ratio)) for stratum in viirs.stratum]
            viirs["converted"] = viirs.n.to_numpy(float) * np.asarray(weights)
            selected = viirs.groupby("date").converted.sum().reindex(dates, fill_value=0).to_numpy(float)
            require(metrics(reference, reference, dates)["tv"] == 0, "Identity changed monthly shape")
            raw_metrics = metrics(reference, raw, dates)
            b1_metrics = metrics(reference, raw * ratio, dates)
            require(abs(raw_metrics["tv"] - b1_metrics["tv"]) <= 1e-12,
                    "Constant scaling changed normalized monthly shape")
            for name, values in (("raw", raw_metrics), ("B1", b1_metrics),
                                 ("selected", metrics(reference, selected, dates))):
                annual.append({"country": country, "year": year, "alternative": name, **values})
    yearly = pd.DataFrame(annual)
    summary = yearly.groupby(["country", "alternative"], sort=True).agg(
        mean_tv=("tv", "mean"), mean_abs_annual_error=("abs_annual_error", "mean"),
        mean_monthly_mae=("monthly_mae", "mean"), peak_agreement=("peak_agreement", "sum"),
    ).reset_index()
    receipt = {
        "scope": "Reproduction of existing whole-year substitution example; unmasked retrospective 2020-2024",
        "countries": list(COUNTRIES), "years": list(YEARS),
        "reference": "Observed MODIS Aqua detections; not ground truth",
        "comparison": "B1 global ratio versus frozen selected model (M1 for India and Nepal); raw is also retained",
        "units": "mean_tv and mean_abs_annual_error are fractions; multiply each by 100 for the story numbers",
        "averaging": "Equal arithmetic mean across five annual comparisons; peak_agreement is a count of years",
        "outage_mask": "None: preserves the original example. Separate outage sensitivity is required.",
        "archive_manifest_fingerprint": model["archive_manifest_fingerprint"],
        "selected_models": {c: model["selection"][c]["selected"] for c in COUNTRIES},
        "input_sha256": {name: digest(repo / name) for name in INPUTS},
        "script_sha256_lf": hashlib.sha256(Path(__file__).read_bytes().replace(b"\r\n", b"\n")).hexdigest(),
        "annual_metrics": annual,
    }
    return summary, receipt


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[1])
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check", action="store_true")
    parser.add_argument("--reference-summary", type=Path)
    args = parser.parse_args()
    repo = args.repo.resolve()
    summary, receipt = reproduce(repo)
    if args.reference_summary:
        compare(summary, pd.read_csv(args.reference_summary))
        print("Original experiment: all six summary columns match for India and Nepal.")
    if args.check:
        compare(summary, pd.read_csv(repo / DESTINATION))
        saved = json.loads((repo / RECEIPT).read_text(encoding="utf-8"))
        require(saved["input_sha256"] == receipt["input_sha256"], "Recorded input hashes changed")
        require(saved["script_sha256_lf"] == receipt["script_sha256_lf"], "Recorded script hash changed")
        print("PASS: saved unmasked whole-year example and source hashes reproduced.")
    elif args.write:
        (repo / DESTINATION).parent.mkdir(parents=True, exist_ok=True)
        summary.to_csv(repo / DESTINATION, index=False, float_format="%.17g", lineterminator="\n")
        (repo / RECEIPT).write_text(json.dumps(receipt, indent=2, allow_nan=False) + "\n", encoding="utf-8")
        print(f"Wrote {DESTINATION} and {RECEIPT}")
    print(summary.to_csv(index=False, float_format="%.10g", lineterminator="\n"), end="")


if __name__ == "__main__":
    main()
