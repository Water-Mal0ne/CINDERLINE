"""Repeat the existing retrospective season experiment on common outage calendars.

Run from the repository root: python -m pipeline.review.season_check
No fitting, downloading, application edits, or official-output writes occur.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

COUNTRIES = ("Australia", "Bangladesh", "Brazil", "Egypt", "India", "Nepal", "United_States")
YEARS = tuple(range(2020, 2025))
MODELS = ("raw", "B1", "selected")
TOL = 1e-12
# Exact frozen local-date labels, not inferred from this season result.
RANGES = (
    ("Aqua", "2020-08-16", "2020-09-02"),
    ("Aqua", "2022-03-31", "2022-04-16"),
    ("VIIRS", "2022-07-26", "2022-08-10"),
    ("VIIRS", "2024-07-09", "2024-07-16"),
    ("VIIRS", "2024-07-24", "2024-08-01"),
    ("VIIRS", "2024-05-31", "2024-06-02"),
    ("VIIRS", "2024-11-04", "2024-11-05"),
)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def json_write(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def csv_write(path, frame):
    frame.to_csv(path, index=False, float_format="%.17g", lineterminator="\n")


def outage_masks():
    masks = {"unmasked": pd.DatetimeIndex([])}
    for name, padding in (("primary", 0), ("padded", 1)):
        dates = set()
        for _, first, last in RANGES:
            dates.update(pd.date_range(pd.Timestamp(first) - pd.Timedelta(days=padding),
                                       pd.Timestamp(last) + pd.Timedelta(days=padding)))
        masks[name] = pd.DatetimeIndex(sorted(dates))
    require(len(masks["primary"]) == 73 and len(masks["padded"]) == 87, "Frozen mask size changed")
    require(set(masks["primary"]).issubset(masks["padded"]), "Padding lost excluded dates")
    return masks


def monthly(values, dates):
    return np.array([values[dates.month == month].sum() for month in range(1, 13)], dtype=float)


def outcomes(reference, candidate, dates):
    """Original sum/share estimand, restricted to the identical retained dates.

    A zero recorded month with retained dates is valid. A month with NO retained
    dates is missing support, never silently interpreted as zero activity.
    """
    reference, candidate = np.asarray(reference, float), np.asarray(candidate, float)
    require(len(reference) == len(candidate) == len(dates), "Mismatched paired daily support")
    require(dates.is_unique and dates.is_monotonic_increasing, "Duplicate or unsorted retained dates")
    require(np.isfinite(reference).all() and np.isfinite(candidate).all(), "Nonfinite outcome input")
    require((reference >= 0).all() and (candidate >= 0).all(), "Negative outcome input")
    ref_m, cand_m = monthly(reference, dates), monthly(candidate, dates)
    ref_total, cand_total = float(reference.sum()), float(candidate.sum())
    require(np.isclose(ref_m.sum(), ref_total, rtol=1e-12, atol=1e-8)
            and np.isclose(cand_m.sum(), cand_total, rtol=1e-12, atol=1e-8), "Monthly/daily sum mismatch")
    missing = [m for m in range(1, 13) if not (dates.month == m).any()]
    reason = ("zero_retained_month:" + ",".join(map(str, missing))) if missing else (
        "zero_reference_total" if ref_total == 0 else "zero_candidate_total" if cand_total == 0 else None)
    tv = None if reason else float(0.5 * np.abs(ref_m / ref_total - cand_m / cand_total).sum())
    ref_peaks = [] if ref_total == 0 or missing else (np.flatnonzero(np.abs(ref_m - ref_m.max()) <= TOL) + 1).tolist()
    cand_peaks = [] if cand_total == 0 or missing else (np.flatnonzero(np.abs(cand_m - cand_m.max()) <= TOL) + 1).tolist()
    signed = None if ref_total == 0 else (cand_total - ref_total) / ref_total
    return dict(tv=tv, undefined_reason=reason, reference_total=ref_total, candidate_total=cand_total,
                annual_relative_error=signed, annual_absolute_relative_error=None if signed is None else abs(signed),
                monthly_mae=None if missing else float(np.abs(ref_m - cand_m).mean()),
                reference_peak_months=json.dumps(ref_peaks), candidate_peak_months=json.dumps(cand_peaks),
                peak_month_agrees=None if reason else bool(set(ref_peaks) & set(cand_peaks)))


def summarize(block):
    result = {"n_scenarios": int(len(block) // 3)}
    pivot = block.pivot(index=["country", "year", "cut_month"], columns="alternative", values="tv")
    for name in MODELS:
        sub = block[block.alternative.eq(name)]
        result.update({f"{name}_mean_tv": float(sub.tv.mean()), f"{name}_median_tv": float(sub.tv.median()),
                       f"{name}_mean_annual_relative_error": float(sub.annual_relative_error.mean()),
                       f"{name}_mean_annual_absolute_relative_error": float(sub.annual_absolute_relative_error.mean()),
                       f"{name}_mean_monthly_mae": float(sub.monthly_mae.mean()),
                       f"{name}_peak_agreement_count": int(sub.peak_month_agrees.sum())})
    for comparator in ("raw", "B1"):
        delta = pivot.selected - pivot[comparator]
        result.update({f"selected_vs_{comparator}_mean_difference": float(delta.mean()),
                       f"selected_vs_{comparator}_median_difference": float(delta.median()),
                       f"selected_vs_{comparator}_improved": int((delta < -TOL).sum()),
                       f"selected_vs_{comparator}_tied": int((delta.abs() <= TOL).sum()),
                       f"selected_vs_{comparator}_worsened": int((delta > TOL).sum()),
                       f"selected_vs_{comparator}_undefined": int(delta.isna().sum())})
    return result


def compare_original(actual, expected):
    keys = ["country", "year", "cut_month", "alternative"]
    actual = actual.sort_values(keys).reset_index(drop=True)
    expected = expected.sort_values(keys).reset_index(drop=True)
    require(actual[keys].equals(expected[keys]), "Original scenario identities changed")
    largest = {}
    for column in expected.columns.difference(keys):
        if pd.api.types.is_numeric_dtype(expected[column]) and column not in {"peak_month_agrees", "undefined_reason"}:
            a, b = actual[column].to_numpy(float), expected[column].to_numpy(float)
            require(np.allclose(a, b, rtol=1e-12, atol=1e-10, equal_nan=True), f"Original outcome changed: {column}")
            largest[column] = float(np.nanmax(np.abs(a - b)))
        else:
            require(actual[column].fillna("").astype(str).equals(expected[column].fillna("").astype(str)),
                    f"Original metadata outcome changed: {column}")
    return largest


def make_report(output, whole, country, coverage, summary):
    lines = ["# Season preservation under common outage masks", "",
             "The original retrospective comparison is reproduced without fitting or selecting a model. "
             "The same retained local dates are used for Aqua and every VIIRS alternative. "
             "The primary mask removes 73 excluded dates from documented outages and previously flagged common zero-detection days; "
             "the padded sensitivity removes 87 dates after expanding each interval by one day at both ends.", "",
             "## Does the original India/Nepal example survive?", "",
             "The comparison below is **B1 versus the frozen selected M1**, using the separate whole-year "
             "replacement control, averaged equally across 2020–2024. TV × 100 is monthly-pattern disagreement "
             "in points, not a percentage of actual fires. Annual error × 100 is absolute relative count "
             "disagreement with Aqua on retained dates; masked totals are not complete calendar-year totals.", "",
             "| Country | Calendar | B1 annual error (%) | Selected annual error (%) | B1 TV (points) | Selected TV (points) |",
             "|---|---|---:|---:|---:|---:|"]
    for c in ("India", "Nepal"):
        for mask in ("unmasked", "primary", "padded"):
            b = whole[(whole.country == c) & (whole['mask'] == mask)].set_index("alternative")
            lines.append(f"| {c} | {mask} | {100*b.loc['B1','mean_abs_annual_error']:.4f} | "
                         f"{100*b.loc['selected','mean_abs_annual_error']:.4f} | {100*b.loc['B1','mean_tv']:.4f} | "
                         f"{100*b.loc['selected','mean_tv']:.4f} |")
    d = summary["direction_checks"]
    lines += ["", f"India's better-total / worse-monthly-shape direction survives both masks: **{d['India']['both_masks_preserve_direction']}**. "
              f"Nepal's lower monthly TV direction survives both masks: **{d['Nepal']['both_masks_preserve_direction']}**. "
              "These are descriptive direction checks, not new significance tests or a claim that every year/cut improves.", "",
              "## All countries and within-year scenarios", "",
              "February–December cuts remain the primary artificial handover scenarios. Each country contributes "
              "55 dependent cuts per calendar. Raw, B1 and selected outputs and all year-level outcomes are retained; "
              "January whole-year and next-January no-handover controls stay separate.", "",
              "| Country | Mask | Raw TV | B1 TV | Selected TV | Selected better / tied / worse vs B1 |",
              "|---|---|---:|---:|---:|---|"]
    for row in country.to_dict("records"):
        lines.append(f"| {row['country']} | {row['mask']} | {100*row['raw_mean_tv']:.4f} | "
                     f"{100*row['B1_mean_tv']:.4f} | {100*row['selected_mean_tv']:.4f} | "
                     f"{row['selected_vs_B1_improved']} / {row['selected_vs_B1_tied']} / {row['selected_vs_B1_worsened']} |")
    lines += ["", "All TV entries above are disagreement points (TV × 100). "
              "Australia, Brazil and the United States retain B1; their selected outputs must coincide with B1.", "",
              "## Coverage and limitations", "",
              f"All 35 country-years retain every month under both masks. The minimum retained month has "
              f"{int(coverage.retained_days.min())} dates. The output includes {summary['total_rows']:,} scenario rows "
              "across the original and two masked calendars, including all controls. "
              "A zero-recorded-count retained day stays zero; an excluded date contributes to neither series. "
              "If any month had no retained dates, TV and peak agreement would be explicitly undefined rather than zero.", "",
              "- The experiment is retrospective: these 2020–2024 years were already examined. It is not a new holdout, "
              "independent preregistration, or a validation of actual fires.",
              "- Aqua is the observation reference, not ground truth. Satellite sensitivity, cloud cover, overpass timing "
              "and remaining processing gaps can affect both streams.",
              "- Exact outage labels are interpreted as local dates, while source notices may use UTC. One-day padding "
              "tests that boundary choice; it does not certify complete observation exposure.",
              "- The mask includes 38 VIIRS dates (33 documented and five previously flagged common zero dates) and "
              "35 Aqua dates. It is a common union applied to every country and alternative, not an effect-selected mask.",
              "- Monthly shares use observed sums on retained days, with no extrapolation or new rate normalization. "
              "A shared mask improves comparability but can remove seasonal information unevenly.",
              "- Cuts reuse the same data; no p-values or independent-trial claims are made. Passing a mean direction "
              "does not imply improvement for every cut, year, metric or country.",
              "- Source support is the preserved, already reconciled national sufficient-statistics dataset. This "
              "rerun does not download/re-clean raw archives or refit official ratios, gates or model selection.", "",
              "## Reproduce and inspect", "", "```sh", "python -m pipeline.review.season_check",
              "python scripts/verify_season_check.py", "```", "",
              "`source_snapshot.json` pins original inputs; `input_manifest.json` records current hashes. "
              "`original_scenarios.csv`, `original_all_country_whole_year_comparison.csv` and `original_protocol.md` preserve "
              "the unmasked baseline. `frozen_outage_dates.csv` is the exact prior 73/87-date record. "
              "`scenarios.csv`, `whole_year_comparison.csv`, `country_summary.csv`, `year_summary.csv`, "
              "`monthly_coverage.csv`, `excluded_dates.csv`, `summary.json` and `invariant_checks.json` expose the rerun. "
              "Independent verification is reported separately; this script does not assert its own independent approval."]
    (output / "SEASON_CHECK.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def run(repo, output):
    output.mkdir(parents=True, exist_ok=True)
    source = repo / "reports/review/season"
    snapshot = json.loads((source / "source_snapshot.json").read_text())
    hashes = {name: sha(repo / name) for name in snapshot["input_sha256"]}
    require(hashes == snapshot["input_sha256"], "Original input hashes changed")
    for filename, key in (("original_protocol.md", "original_protocol_sha256"),
                          ("original_scenarios.csv", "original_scenario_sha256"),
                          ("original_all_country_whole_year_comparison.csv", "original_whole_year_sha256"),
                          ("frozen_outage_dates.csv", "frozen_outage_dates_sha256")):
        require(sha(source / filename) == snapshot[key], f"Preserved baseline changed: {filename}")
    masks = outage_masks()
    excluded = pd.DataFrame([{"mask": name, "date": date.date().isoformat()}
                             for name, dates in masks.items() for date in dates])
    require(excluded.equals(pd.read_csv(source / "frozen_outage_dates.csv")), "Exact frozen date lists changed")
    model = json.loads((repo / "reports/harmonization_model.json").read_text())
    selection = json.loads((repo / "reports/selection_lock.json").read_text())
    locks = json.loads((repo / "reports/LOCKED_ARTIFACTS.json").read_text())["sha256"]
    require(all(sha(repo / "reports" / name) == value for name, value in locks.items()), "Locked artifact changed")
    require(model["ratios"] == selection["ratios"] and model["selection"] == selection["selection"], "Frozen choices differ")
    require(model["archive_manifest_fingerprint"] == selection["archive_manifest_fingerprint"], "Model provenance differs")
    counts = pd.read_parquet(repo / "data/sample/seven_country_national_counts.parquet")
    require(counts.attrs.get("archive_manifest_fingerprint") == model["archive_manifest_fingerprint"], "Count provenance differs")
    require(counts.attrs.get("label") == "REAL FIRMS DATA", "Not real FIRMS inputs")
    counts["date"] = pd.to_datetime(counts.date)
    require(counts.cell_id.eq("ALL").all() and counts.year.eq(counts.date.dt.year).all(), "Incorrect national/local-year input")
    require(np.isfinite(counts.n).all() and counts.n.ge(0).all() and np.equal(counts.n, np.floor(counts.n)).all(), "Invalid counts")
    ratio = float(model["ratios"]["B1"])
    require(np.isfinite(ratio) and ratio > 0, "Invalid global ratio")
    started = datetime.now(timezone.utc).isoformat()
    manifest = dict(started_utc=started, input_sha256=hashes,
                    script_sha256_lf=hashlib.sha256(Path(__file__).read_bytes().replace(b"\r\n", b"\n")).hexdigest(),
                    source_snapshot_sha256=sha(source / "source_snapshot.json"), countries=list(COUNTRIES), years=list(YEARS),
                    selected_models={c: model["selection"][c]["selected"] for c in COUNTRIES},
                    ranges=[list(r) for r in RANGES], mask_sizes={n: len(d) for n, d in masks.items()},
                    note="Existing retrospective outcomes reproduced, then restricted to frozen common dates; no refitting.")
    json_write(output / "input_manifest.json", manifest)
    records, coverage, daily = [], [], []
    for country in COUNTRIES:
        chosen = model["selection"][country]["selected"]
        require(chosen in {"B1", "M1"}, "Unsupported selected model")
        for year in YEARS:
            dates = pd.date_range(f"{year}-01-01", f"{year}-12-31")
            subset = counts[counts.country.eq(country) & counts.year.eq(year)]
            require(set(subset.stream) >= {"Aqua", "VIIRS"}, "Country-year source missing")
            aqua = subset[subset.stream.eq("Aqua")]
            viirs = subset[subset.stream.eq("VIIRS")].copy()
            reference = aqua.groupby("date").n.sum().reindex(dates, fill_value=0).to_numpy(float)
            raw = viirs.groupby("date").n.sum().reindex(dates, fill_value=0).to_numpy(float)
            weights = np.array([ratio if chosen == "B1" else model["ratios"]["M1"].get(f"{country}|{stratum}", ratio)
                                for stratum in viirs.stratum], dtype=float)
            require(np.isfinite(weights).all() and (weights > 0).all(), "Invalid frozen weight")
            viirs["weighted"] = viirs.n.to_numpy(float) * weights
            selected = viirs.groupby("date").weighted.sum().reindex(dates, fill_value=0).to_numpy(float)
            b1 = raw * ratio
            if chosen == "B1":
                require(np.allclose(selected, b1, rtol=1e-12, atol=1e-8), "B1-selected values differ")
            for i, date in enumerate(dates):
                daily.append(dict(country=country, year=year, date=date.date().isoformat(), Aqua=reference[i],
                                  raw=raw[i], B1=b1[i], selected=selected[i]))
            for mask, excluded_dates in masks.items():
                keep = ~dates.isin(excluded_dates)
                retained = dates[keep]
                ref = reference[keep]
                alternatives = {"raw": raw[keep], "B1": b1[keep], "selected": selected[keep]}
                for month in range(1, 13):
                    total = int((dates.month == month).sum())
                    left = int((retained.month == month).sum())
                    coverage.append(dict(mask=mask, country=country, year=year, month=month,
                                         calendar_days=total, excluded_days=total-left, retained_days=left))
                for cut_month in range(1, 14):
                    cutoff = pd.Timestamp(year + 1, 1, 1) if cut_month == 13 else pd.Timestamp(year, cut_month, 1)
                    kind = "whole_year" if cut_month == 1 else "no_handover" if cut_month == 13 else "within_year"
                    after = retained >= cutoff
                    for alternative, values in alternatives.items():
                        candidate = np.where(after, values, ref)
                        require(np.isclose(candidate.sum(), ref[~after].sum()+values[after].sum(), rtol=1e-12, atol=1e-8), "Stitch sum mismatch")
                        result = outcomes(ref, candidate, retained)
                        if kind == "no_handover" and result["undefined_reason"] is None:
                            require(result["tv"] <= TOL and abs(result["annual_relative_error"]) <= TOL, "No-handover control failed")
                        records.append(dict(mask=mask, country=country, year=year, selected_model=chosen,
                                            retained_days=len(retained), cut_month=cut_month, cut_date=cutoff.date().isoformat(),
                                            scenario_kind=kind, alternative=alternative, **result))
                raw_tv = outcomes(ref, alternatives["raw"], retained)["tv"]
                b1_tv = outcomes(ref, alternatives["B1"], retained)["tv"]
                require(raw_tv is None and b1_tv is None or abs(raw_tv-b1_tv) <= TOL, "Whole-year B1 changed normalized shape")
    scenarios, coverage = pd.DataFrame(records), pd.DataFrame(coverage)
    require(len(scenarios) == 4095, "Unexpected scenario count")
    csv_write(output / "scenarios.csv", scenarios)
    csv_write(output / "monthly_coverage.csv", coverage)
    csv_write(output / "excluded_dates.csv", excluded)
    csv_write(output / "daily_inputs.csv", pd.DataFrame(daily))
    # Undefined results have already been exported above; do not summarize them as a pass.
    require(scenarios.tv.notna().all(), "Undefined real scenario: inspect exported outcomes and month coverage")
    differences = compare_original(scenarios[scenarios['mask'].eq("unmasked")], pd.read_csv(source / "original_scenarios.csv"))
    primary = scenarios[scenarios.scenario_kind.eq("within_year")]
    country_summary = pd.DataFrame([dict(mask=mask, country=c, selected_model=model["selection"][c]["selected"], **summarize(block))
                                    for (mask, c), block in primary.groupby(["mask", "country"], sort=False)])
    year_summary = pd.DataFrame([dict(mask=mask, country=c, year=int(y), **summarize(block))
                                 for (mask, c, y), block in primary.groupby(["mask", "country", "year"], sort=False)])
    whole = scenarios[scenarios.scenario_kind.eq("whole_year")].groupby(["mask", "country", "alternative"], sort=False).agg(
        mean_tv=("tv", "mean"), mean_abs_annual_error=("annual_absolute_relative_error", "mean"),
        mean_monthly_mae=("monthly_mae", "mean"), peak_agreement=("peak_month_agrees", "sum")).reset_index()
    original_whole = pd.read_csv(source / "original_all_country_whole_year_comparison.csv").sort_values(["country", "alternative"]).reset_index(drop=True)
    new_whole = whole[whole['mask'].eq("unmasked")].sort_values(["country", "alternative"]).reset_index(drop=True)
    for col in ("mean_tv", "mean_abs_annual_error", "mean_monthly_mae", "peak_agreement"):
        require(np.allclose(new_whole[col], original_whole[col], rtol=1e-12, atol=1e-10), f"Original whole-year summary differs: {col}")
    direction = {}
    for c in ("India", "Nepal"):
        by_mask = {}
        for mask in masks:
            table = whole[(whole.country == c) & (whole['mask'] == mask)].set_index("alternative")
            tv_delta = float(table.loc["selected", "mean_tv"] - table.loc["B1", "mean_tv"])
            error_delta = float(table.loc["selected", "mean_abs_annual_error"] - table.loc["B1", "mean_abs_annual_error"])
            by_mask[mask] = dict(selected_minus_B1_mean_tv=tv_delta, selected_minus_B1_mean_abs_annual_error=error_delta,
                                 preserves_original_direction=bool(tv_delta > TOL and error_delta < -TOL) if c == "India" else bool(tv_delta < -TOL))
        direction[c] = dict(calendars=by_mask, both_masks_preserve_direction=all(by_mask[m]["preserves_original_direction"] for m in ("primary", "padded")))
    summary = dict(design="Retrospective, frozen-model common-date sensitivity; no independent-trial inference", total_rows=len(scenarios),
                   eligible_country_years=35, primary_paired_scenarios_per_mask=385, alternative_rows_per_mask=1365,
                   mask_sizes={n: len(d) for n, d in masks.items()}, min_retained_days_per_month=int(coverage.retained_days.min()),
                   zero_coverage_months=int(coverage.retained_days.eq(0).sum()), undefined_scenarios=int(scenarios.tv.isna().sum()),
                   direction_checks=direction, original_scenario_max_abs_differences=differences,
                   primary={m: summarize(primary[primary['mask'].eq(m)]) for m in masks},
                   finished_utc=datetime.now(timezone.utc).isoformat(), independently_verified=False)
    for filename, frame in (("country_summary.csv", country_summary), ("year_summary.csv", year_summary), ("whole_year_comparison.csv", whole)):
        csv_write(output / filename, frame)
    json_write(output / "summary.json", summary)
    require({name: sha(repo / name) for name in hashes} == hashes, "Inputs changed during run")
    json_write(output / "invariant_checks.json", dict(passed=True, original_rows_reproduced=1365,
        checks=["original input and lock hashes", "source and local-year identities", "all finite nonnegative frozen inputs",
                "exact frozen primary/padded dates", "same dates for reference and every alternative", "all original scenarios and whole-year summaries",
                "all no-handover controls", "all B1 whole-year shape invariants", "all B1-selected daily values", "unchanged input hashes after run"],
        original_scenario_max_abs_differences=differences))
    make_report(output, whole, country_summary, coverage, summary)
    print(json.dumps({"direction_checks": direction, "original_max_abs_differences": differences,
                      "mask_sizes": summary["mask_sizes"], "min_retained_days_per_month": summary["min_retained_days_per_month"]}, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    repo = args.repo.resolve()
    run(repo, args.output.resolve() if args.output else repo / "reports/review/season")


if __name__ == "__main__":
    main()
