"""Independently reproduce the retrospective season experiment from frozen inputs.

No primary analysis or application functions are imported. Pandas only reads and
writes tables; daily weights, monthly sums and metrics use independent Python
loops/math.fsum. This verifies reproduction, not external scientific validation.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
import hashlib
import json
import math
from pathlib import Path
import statistics

import pandas as pd

COUNTRIES = ("Australia", "Bangladesh", "Brazil", "Egypt", "India", "Nepal", "United_States")
ALTERNATIVES = ("raw", "B1", "selected")
YEARS = tuple(range(2020, 2025))
TOL = 1e-12
OUTAGES = (
    ("2020-08-16", "2020-09-02"),
    ("2022-03-31", "2022-04-16"),
    ("2022-07-26", "2022-08-10"),
    ("2024-07-09", "2024-07-16"),
    ("2024-07-24", "2024-08-01"),
    ("2024-05-31", "2024-06-02"),
    ("2024-11-04", "2024-11-05"),
)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def demand(condition, message):
    if not condition:
        raise AssertionError(message)


def write_json(path, obj):
    path.write_text(json.dumps(obj, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def dates_between(first, last):
    return [first + timedelta(days=n) for n in range((last - first).days + 1)]


def exclusions(padding):
    return set().union(*(set(dates_between(date.fromisoformat(a) - timedelta(days=padding),
                                          date.fromisoformat(b) + timedelta(days=padding)))
                         for a, b in OUTAGES))


def fingerprint(manifest):
    fields = ("country", "sensor", "year", "sha256", "complete", "status")
    rows = [{key: row.get(key) for key in fields} for row in manifest["files"]]
    rows.sort(key=lambda row: (str(row["country"]), str(row["sensor"]), int(row["year"] or 0)))
    return hashlib.sha256(json.dumps(rows, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def metrics(reference, candidate, coverage):
    demand(len(reference) == len(candidate) == len(coverage) == 12, "Expected twelve monthly values")
    demand(all(math.isfinite(x) and x >= 0 for x in (*reference, *candidate)), "Invalid monthly values")
    demand(all(n > 0 for n in coverage), "A fully excluded month cannot be treated as observed zero")
    ref_total, cand_total = math.fsum(reference), math.fsum(candidate)
    reason = "zero_reference_total" if ref_total == 0 else "zero_candidate_total" if cand_total == 0 else None
    tv = None if reason else math.fsum(abs(a / ref_total - b / cand_total)
                                     for a, b in zip(reference, candidate)) / 2
    ref_peaks = [] if ref_total == 0 else [i + 1 for i, x in enumerate(reference) if abs(x - max(reference)) <= TOL]
    cand_peaks = [] if cand_total == 0 else [i + 1 for i, x in enumerate(candidate) if abs(x - max(candidate)) <= TOL]
    signed = None if ref_total == 0 else (cand_total - ref_total) / ref_total
    return dict(tv=tv, undefined_reason=reason, reference_total=ref_total, candidate_total=cand_total,
                annual_relative_error=signed, annual_absolute_relative_error=None if signed is None else abs(signed),
                monthly_mae=math.fsum(abs(a - b) for a, b in zip(reference, candidate)) / 12,
                reference_peak_months=json.dumps(ref_peaks), candidate_peak_months=json.dumps(cand_peaks),
                peak_month_agrees=bool(set(ref_peaks).intersection(cand_peaks)))


def mean(values):
    return math.fsum(values) / len(values) if values else None


def summarize(rows):
    result = {"n_scenarios": len(rows) // 3}
    lookup = {(r["country"], r["year"], r["cut_month"], r["alternative"]): r for r in rows}
    for alt in ALTERNATIVES:
        sub = [r for r in rows if r["alternative"] == alt]
        for field in ("tv", "annual_relative_error", "annual_absolute_relative_error", "monthly_mae"):
            result[f"{alt}_mean_{field}"] = mean([r[field] for r in sub if r[field] is not None])
        finite_tv = [r["tv"] for r in sub if r["tv"] is not None]
        result[f"{alt}_median_tv"] = statistics.median(finite_tv) if finite_tv else None
        result[f"{alt}_peak_agreement_count"] = sum(r["peak_month_agrees"] for r in sub)
    for comparator in ("raw", "B1"):
        delta, undefined = [], 0
        for r in rows:
            if r["alternative"] != "selected":
                continue
            other = lookup[(r["country"], r["year"], r["cut_month"], comparator)]
            if r["tv"] is None or other["tv"] is None:
                undefined += 1
            else:
                delta.append(r["tv"] - other["tv"])
        result.update({f"selected_vs_{comparator}_{key}": value for key, value in {
            "mean_difference": mean(delta), "median_difference": statistics.median(delta) if delta else None,
            "improved": sum(x < -TOL for x in delta), "tied": sum(abs(x) <= TOL for x in delta),
            "worsened": sum(x > TOL for x in delta), "undefined": undefined}.items()})
    return result


def compare_csv(expected_rows, target, keys, *, ignored=()):
    actual = pd.read_csv(target, keep_default_na=False).to_dict("records")
    def key(row):
        return tuple(str(row[k]) for k in keys)
    lookup = {key(row): row for row in actual}
    reference = {key(row): row for row in expected_rows}
    demand(len(lookup) == len(actual), f"Duplicate keys in {target.name}")
    demand(len(reference) == len(expected_rows), f"Duplicate independent keys for {target.name}")
    missing, extra = sorted(set(reference) - set(lookup)), sorted(set(lookup) - set(reference))
    failures, mismatch_count, maxima, checked_fields = [], 0, {}, set()
    for k in reference.keys() & lookup.keys():
        for field, expected in reference[k].items():
            if field in ignored:
                continue
            found = lookup[k].get(field)
            checked_fields.add(field)
            equal = False
            if expected is None:
                equal = found in (None, "") or (isinstance(found, float) and math.isnan(found))
            elif field.endswith("peak_months"):
                equal = json.loads(expected) == json.loads(found) if found else False
            elif isinstance(expected, bool):
                equal = str(found).lower() == str(expected).lower()
            elif isinstance(expected, int):
                equal = found == expected
                maxima[field] = max(maxima.get(field, 0), abs(float(found) - expected)) if found is not None else None
            elif isinstance(expected, float):
                equal = isinstance(found, (int, float)) and math.isclose(expected, found, rel_tol=1e-11, abs_tol=1e-8)
                maxima[field] = max(maxima.get(field, 0), abs(float(found) - expected)) if found is not None else None
            else:
                equal = str(found) == str(expected)
            if not equal:
                mismatch_count += 1
                if len(failures) < 30:
                    failures.append(dict(key=k, field=field, expected=expected, actual=found))
    return dict(rows_expected=len(expected_rows), rows_actual=len(actual), fields_checked=sorted(checked_fields),
                missing_keys=missing, extra_keys=extra, mismatch_count=mismatch_count, mismatch_examples=failures,
                max_absolute_difference_by_field=maxima, passed=not missing and not extra and not mismatch_count)


def compare_json(expected, actual):
    failures, maximum, checked = [], 0.0, 0
    def walk(wanted, found, path):
        nonlocal maximum, checked
        if isinstance(wanted, dict):
            if not isinstance(found, dict):
                failures.append(dict(path=path, expected=wanted, actual=found))
                return
            for key, value in wanted.items():
                walk(value, found.get(key), path + "." + key)
            return
        checked += 1
        if isinstance(wanted, float) and isinstance(found, (int, float)):
            maximum = max(maximum, abs(wanted - found))
            equal = math.isclose(wanted, found, rel_tol=1e-11, abs_tol=1e-8)
        else:
            equal = wanted == found
        if not equal:
            failures.append(dict(path=path, expected=wanted, actual=found))
    walk(expected, actual, "root")
    return dict(fields_checked=checked, mismatch_count=len(failures), mismatch_examples=failures[:30],
                max_absolute_numeric_difference=maximum, passed=not failures)


def synthetic_checks():
    ref = list(range(1, 13))
    identity = metrics(ref, ref, [30] * 12)
    scaled = metrics(ref, [3 * v for v in ref], [30] * 12)
    demand(identity["tv"] == 0 and identity["annual_relative_error"] == 0, "Identity fixture failed")
    demand(scaled["tv"] <= TOL and scaled["annual_relative_error"] == 2, "Shape-versus-scale fixture failed")
    demand(metrics([0] * 12, ref, [30] * 12)["undefined_reason"] == "zero_reference_total", "Zero reference fixture failed")
    demand(metrics(ref, [0] * 12, [30] * 12)["undefined_reason"] == "zero_candidate_total", "Zero candidate fixture failed")
    demand(json.loads(metrics([1] * 12, [1] * 12, [30] * 12)["reference_peak_months"]) == list(range(1, 13)), "Peak tie fixture failed")
    try:
        metrics(ref, ref, [0] + [30] * 11)
    except AssertionError:
        pass
    else:
        raise AssertionError("Empty-month guard fixture failed")
    return ["identity", "whole-year scale preserves normalized shape", "zero reference explicit", "zero candidate explicit",
            "all tied peak months retained", "fully excluded month rejected"]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--report-dir", type=Path)
    parser.add_argument("--reconstruct-only", action="store_true", help="Write independent tables before primary outputs exist")
    args = parser.parse_args()
    root = args.repo_root.resolve()
    reports = args.report_dir.resolve() if args.report_dir else root / "reports/review/season"
    out = reports / "verification"
    out.mkdir(parents=True, exist_ok=True)
    snapshot = json.loads((reports / "source_snapshot.json").read_text())
    input_hashes = {name: sha(root / name) for name in snapshot["input_sha256"]}
    demand(input_hashes == snapshot["input_sha256"], "Frozen input hash mismatch")
    preserved = {"original_protocol.md": "original_protocol_sha256", "original_scenarios.csv": "original_scenario_sha256",
                 "original_all_country_whole_year_comparison.csv": "original_whole_year_sha256", "frozen_outage_dates.csv": "frozen_outage_dates_sha256"}
    for name, key in preserved.items():
        demand(sha(reports / name) == snapshot[key], f"Preserved source changed: {name}")
    model = json.loads((root / "reports/harmonization_model.json").read_text())
    lock = json.loads((root / "reports/selection_lock.json").read_text())
    locks = json.loads((root / "reports/LOCKED_ARTIFACTS.json").read_text())["sha256"]
    demand(all(sha(root / "reports" / name) == expected for name, expected in locks.items()), "Locked scientific artifact changed")
    demand(model["ratios"] == lock["ratios"] and model["selection"] == lock["selection"], "Model differs from frozen selection")
    counts_path = root / "data/sample/seven_country_national_counts.parquet"
    counts = pd.read_parquet(counts_path)
    manifest_path = root / "data/sample/seven_country_manifest.json"
    manifest = json.loads(manifest_path.read_text())
    fp = fingerprint(manifest)
    demand(fp == model["archive_manifest_fingerprint"] == lock["archive_manifest_fingerprint"] == counts.attrs["archive_manifest_fingerprint"], "Archive identity mismatch")
    demand(counts.attrs["label"] == "REAL FIRMS DATA", "Unexpected data label")
    demand(counts.cell_id.eq("ALL").all(), "Non-national records present")
    demand(counts.n.ge(0).all() and counts.n.eq(counts.n.astype("int64")).all(), "Invalid counts")
    demand(counts.date.dt.year.eq(counts.year).all(), "Year/date mismatch")
    demand(not counts.duplicated(["country", "cell_id", "date", "stratum", "stream"]).any(), "Duplicate sufficient-statistic key")
    masks = {"unmasked": set(), "primary": exclusions(0), "padded": exclusions(1)}
    demand(len(masks["primary"]) == 73 and len(masks["padded"]) == 87, "Unexpected mask sizes")
    frozen_dates = pd.read_csv(reports / "frozen_outage_dates.csv")
    for name in ("primary", "padded"):
        demand(set(frozen_dates.loc[frozen_dates["mask"].eq(name), "date"]) == {d.isoformat() for d in masks[name]}, "Frozen date list differs from independently expanded intervals")
    calendar = dates_between(date(2020, 1, 1), date(2024, 12, 31))
    daily = {(country, d): {"Aqua": 0, "raw": 0, "selected_parts": []} for country in COUNTRIES for d in calendar}
    relevant = counts[counts.country.isin(COUNTRIES) & counts.year.isin(YEARS) & counts.stream.isin(["Aqua", "VIIRS"])]
    for r in relevant.itertuples(index=False):
        d = r.date.date()
        record = daily[(r.country, d)]
        if r.stream == "Aqua":
            record["Aqua"] += int(r.n)
        else:
            record["raw"] += int(r.n)
            selected = model["selection"][r.country]["selected"]
            weight = model["ratios"]["B1"] if selected == "B1" else model["ratios"]["M1"].get(f"{r.country}|{r.stratum}", model["ratios"]["B1"])
            record["selected_parts"].append(int(r.n) * weight)
    daily_records = []
    for (country, d), record in daily.items():
        record["B1"] = record["raw"] * model["ratios"]["B1"]
        record["selected"] = math.fsum(record.pop("selected_parts"))
        daily_records.append(dict(country=country, year=d.year, date=d.isoformat(), **record))
    pd.DataFrame(daily_records).to_csv(out / "independent_daily.csv", index=False, float_format="%.17g")
    scenarios, coverage_rows, monthly_rows = [], [], []
    for mask_name, excluded in masks.items():
        for country in COUNTRIES:
            for year in YEARS:
                monthly = {alt: [] for alt in ("Aqua", *ALTERNATIVES)}
                coverage = []
                for month in range(1, 13):
                    month_dates = [d for d in calendar if d.year == year and d.month == month]
                    retained = [d for d in month_dates if d not in excluded]
                    coverage.append(len(retained))
                    coverage_rows.append(dict(mask=mask_name, country=country, year=year, month=month,
                                              calendar_days=len(month_dates), excluded_days=len(month_dates) - len(retained), retained_days=len(retained)))
                    for alt in monthly:
                        monthly[alt].append(math.fsum(daily[(country, d)][alt] for d in retained))
                    monthly_rows.append(dict(mask=mask_name, country=country, year=year, month=month,
                                             retained_days=len(retained), **{alt: monthly[alt][-1] for alt in monthly}))
                ref = monthly["Aqua"]
                for cut in range(1, 14):
                    for alt in ALTERNATIVES:
                        candidate = [ref[m - 1] if m < cut else monthly[alt][m - 1] for m in range(1, 13)]
                        outcome = metrics(ref, candidate, coverage)
                        demand(outcome["tv"] is not None, "Unexpected undefined real scenario")
                        if cut == 13:
                            demand(outcome["tv"] <= TOL and abs(outcome["annual_relative_error"]) <= TOL, "No-handover control failed")
                        scenarios.append(dict(mask=mask_name, country=country, year=year,
                                              selected_model=model["selection"][country]["selected"], cut_month=cut,
                                              cut_date=date(year + 1, 1, 1).isoformat() if cut == 13 else date(year, cut, 1).isoformat(),
                                              scenario_kind="whole_year" if cut == 1 else "no_handover" if cut == 13 else "within_year",
                                              alternative=alt, retained_days=sum(coverage), **outcome))
                demand(abs(metrics(ref, monthly["raw"], coverage)["tv"] - metrics(ref, monthly["B1"], coverage)["tv"]) <= TOL,
                       "Whole-year scalar B1 unexpectedly changed shape")
    country_summary, year_summary, whole = [], [], []
    for mask_name in masks:
        for country in COUNTRIES:
            sub = [r for r in scenarios if r["mask"] == mask_name and r["country"] == country]
            within = [r for r in sub if r["scenario_kind"] == "within_year"]
            country_summary.append(dict(mask=mask_name, country=country, selected_model=model["selection"][country]["selected"], **summarize(within)))
            for year in YEARS:
                year_summary.append(dict(mask=mask_name, country=country, year=year, **summarize([r for r in within if r["year"] == year])))
            for alt in ALTERNATIVES:
                w = [r for r in sub if r["cut_month"] == 1 and r["alternative"] == alt]
                whole.append(dict(mask=mask_name, country=country, alternative=alt, mean_tv=mean([r["tv"] for r in w]),
                                  mean_abs_annual_error=mean([r["annual_absolute_relative_error"] for r in w]),
                                  mean_monthly_mae=mean([r["monthly_mae"] for r in w]), peak_agreement=sum(r["peak_month_agrees"] for r in w)))
    excluded_rows = [dict(mask=mask_name, date=d.isoformat()) for mask_name, excluded in masks.items() for d in sorted(excluded)]
    tables = {"daily_inputs.csv": (daily_records, ("country", "date")),
              "scenarios.csv": (scenarios, ("mask", "country", "year", "cut_month", "alternative")),
              "country_summary.csv": (country_summary, ("mask", "country")),
              "year_summary.csv": (year_summary, ("mask", "country", "year")),
              "whole_year_comparison.csv": (whole, ("mask", "country", "alternative")),
              "monthly_coverage.csv": (coverage_rows, ("mask", "country", "year", "month")),
              "excluded_dates.csv": (excluded_rows, ("mask", "date"))}
    for filename, (records, _) in tables.items():
        pd.DataFrame(records).to_csv(out / ("independent_" + filename), index=False, float_format="%.17g")
    pd.DataFrame(monthly_rows).to_csv(out / "independent_monthly.csv", index=False, float_format="%.17g")
    agreement = {
        "original_scenarios.csv": compare_csv([r for r in scenarios if r["mask"] == "unmasked"], reports / "original_scenarios.csv",
                                               ("country", "year", "cut_month", "alternative"), ignored=("mask", "retained_days")),
        "original_all_country_whole_year_comparison.csv": compare_csv([r for r in whole if r["mask"] == "unmasked"], reports / "original_all_country_whole_year_comparison.csv",
                                                           ("country", "alternative"), ignored=("mask",))}
    if not args.reconstruct_only:
        for filename, (records, keys) in tables.items():
            agreement[filename] = compare_csv(records, reports / filename, keys)
        direction = {}
        for country in ("India", "Nepal"):
            by_mask = {}
            for mask_name in masks:
                by_alt = {r["alternative"]: r for r in whole if r["country"] == country and r["mask"] == mask_name}
                tv_delta = by_alt["selected"]["mean_tv"] - by_alt["B1"]["mean_tv"]
                total_delta = by_alt["selected"]["mean_abs_annual_error"] - by_alt["B1"]["mean_abs_annual_error"]
                by_mask[mask_name] = dict(selected_minus_B1_mean_tv=tv_delta, selected_minus_B1_mean_abs_annual_error=total_delta,
                                          preserves_original_direction=(tv_delta > TOL and total_delta < -TOL) if country == "India" else tv_delta < -TOL)
            direction[country] = dict(calendars=by_mask, both_masks_preserve_direction=all(by_mask[m]["preserves_original_direction"] for m in ("primary", "padded")))
        expected_summary = dict(total_rows=4095, eligible_country_years=35, primary_paired_scenarios_per_mask=385,
                                alternative_rows_per_mask=1365, mask_sizes={name: len(excluded) for name, excluded in masks.items()},
                                min_retained_days_per_month=min(r["retained_days"] for r in coverage_rows), zero_coverage_months=0,
                                undefined_scenarios=0, direction_checks=direction,
                                primary={name: summarize([r for r in scenarios if r["mask"] == name and r["scenario_kind"] == "within_year"]) for name in masks})
        agreement["summary.json"] = compare_json(expected_summary, json.loads((reports / "summary.json").read_text()))
        analysis_path = root / "pipeline/review/season_check.py"
        expected_manifest = dict(input_sha256=input_hashes, source_snapshot_sha256=sha(reports / "source_snapshot.json"),
                                 countries=list(COUNTRIES), years=list(YEARS), mask_sizes=expected_summary["mask_sizes"],
                                 selected_models={c: model["selection"][c]["selected"] for c in COUNTRIES},
                                 script_sha256_lf=hashlib.sha256(analysis_path.read_bytes().replace(b"\r\n", b"\n")).hexdigest())
        manifest_result = json.loads((reports / "input_manifest.json").read_text())
        agreement["input_manifest.json"] = compare_json(expected_manifest, manifest_result)
        demand([r[1:] for r in manifest_result["ranges"]] == [list(r) for r in OUTAGES], "Manifest intervals differ")
        invariants = json.loads((reports / "invariant_checks.json").read_text())
        agreement["invariant_checks.json"] = compare_json(dict(passed=True, original_rows_reproduced=1365), invariants)
        write_json(out / "independent_summary.json", expected_summary)
    for name, digest in input_hashes.items():
        demand(sha(root / name) == digest, f"Input changed during verification: {name}")
    for name, key in preserved.items():
        demand(sha(reports / name) == snapshot[key], f"Preserved source changed during verification: {name}")
    checks = synthetic_checks()
    all_match = all(result["passed"] for result in agreement.values())
    receipt = dict(status="RECONSTRUCTED" if args.reconstruct_only and all_match else "PASS" if all_match else "FAIL",
                   completed_utc=datetime.now(timezone.utc).isoformat(), verifier_sha256=sha(Path(__file__)),
                   method="Independent national-parquet daily and monthly accumulation with math.fsum; no primary analysis imports; no fitting.",
                   scientific_scope="Retrospective reference comparison. Common retained date labels, unnormalized monthly totals, no ground-truth or causal validation.",
                   source_input_sha256=input_hashes, manifest_sha256=sha(manifest_path), archive_manifest_fingerprint=fp,
                   source_snapshot_sha256=sha(reports / "source_snapshot.json"),
                   preserved_input_sha256={name: sha(reports / name) for name in preserved},
                   mask_excluded_dates={name: len(excluded) for name, excluded in masks.items()},
                   masks_common_to_all_countries_and_streams=True, original_country_years=35, countries=list(COUNTRIES),
                   daily_country_dates=len(daily_records), scenario_rows=len(scenarios), monthly_coverage_rows=len(coverage_rows),
                   all_cuts_per_year=list(range(1, 14)), all_real_scenarios_defined=True,
                   synthetic_checks=checks, agreement=agreement,
                   verified_output_sha256={name: sha(reports / name) for name in (*tables, "summary.json", "input_manifest.json", "invariant_checks.json") if (reports / name).exists()})
    analysis_script = root / "pipeline/review/season_check.py"
    if analysis_script.exists():
        receipt["analysis_script_sha256"] = sha(analysis_script)
    write_json(out / "independent_verification.json", receipt)
    print(json.dumps({"status": receipt["status"], "scenario_rows": len(scenarios),
                      "comparisons": {name: {"rows": r.get("rows_actual"), "passed": r["passed"], "mismatches": r["mismatch_count"]} for name, r in agreement.items()}}, indent=2))
    if not all_match:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
