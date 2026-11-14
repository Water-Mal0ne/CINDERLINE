"""Reproducible, gated weekly patterns in fire detections.

Input dates must already be local CIVIL dates. This module never interprets
an empty detection day as a cloud-free satellite observation.

OFFICIAL DECISION: the gate pre-registered in kill_test.py (team reference script,
reference/kill_test.py). Its outputs (kill_test_gate.json, kill_test_results.csv) are
loaded with load_official() and are the only source of the published decision.

ROBUSTNESS CHECKS: make_gate() below is this module's stricter variant (verified
adjacent-year archives, rest-day 95% upper bound < 1, fixed 21-test Bonferroni family,
matched per-country static-source controls). It is reported NEXT TO the official
decision as robustness checks and never replaces or overrides it.
"""
from __future__ import annotations

import argparse
import hashlib
import html
import json
from pathlib import Path

import numpy as np
import pandas as pd

from pipeline.harmonize import FIRST_COMPLETE_YEAR

DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
STREAMS = ["Terra", "Aqua", "VIIRS"]
REST_DAYS = {"United_States": "Sun", "Australia": "Sun", "Nepal": "Sat",
             "Bangladesh": "Fri", "Egypt": "Fri", "India": "Sun", "Brazil": "Sun"}
DEFAULTS = {"min_years": 5, "min_detections_per_year": 140, "bootstrap_draws": 2000,
            "null_draws": 5000, "seed": 42, "alpha": 0.05, "as_of_year": 2026}
CAVEATS = [
    "Hotspot detections are not independent fires or ignition events.",
    "Cloud cover, satellite outages and overpass exposure are not measured by annual CSV availability.",
    "A weekly association is consistent with human scheduling; it does not establish ignition cause.",
    "Absence of a weekly dip does not establish weather-driven fire.",
    "Terra, Aqua and VIIRS observe overlapping events; agreement is corroboration, not independent replication.",
    "The null test assumes exchangeable weekday labels within each year under the null.",
    "Static industrial sources may have real weekly schedules; controls are diagnostic, not a guaranteed natural null.",
]


def _rng(seed: int, key: str) -> np.random.Generator:
    """Stable per-analysis RNG: results do not depend on country iteration order."""
    digest = hashlib.sha256(key.encode()).digest()
    return np.random.default_rng(np.random.SeedSequence([seed, int.from_bytes(digest[:8], "little")]))


def weekday_exposure(year: int) -> np.ndarray:
    dates = pd.date_range(f"{year}-01-01", f"{year}-12-31", freq="D")
    return np.bincount(dates.day_of_week, minlength=7).astype(float)


def _manifest_dict(manifest) -> dict:
    if manifest is None:
        return {}
    if isinstance(manifest, (str, Path)):
        return json.loads(Path(manifest).read_text(encoding="utf-8"))
    if isinstance(manifest, list):
        return {"files": manifest}
    return manifest


def verified_local_year(manifest: dict, country: str, stream: str, year: int) -> bool:
    """Verify input-period completeness, NOT satellite observation coverage.

    Explicit local_periods may attest an exact local calendar year. Otherwise
    require the annual UTC file plus both adjacent UTC years, conservatively
    covering civil dates near year boundaries in multi-zone countries.
    """
    if stream not in FIRST_COMPLETE_YEAR or year < FIRST_COMPLETE_YEAR[stream]:
        return False
    for entry in manifest.get("local_periods", []):
        if (entry.get("country") == country and entry.get("stream") == stream
                and int(entry.get("year", -1)) == year and entry.get("complete") is True):
            return True
    sensor = "viirs-snpp" if stream == "VIIRS" else "modis"
    completed = set()
    for entry in manifest.get("files", []):
        if (entry.get("country") == country and entry.get("sensor") == sensor
                and entry.get("complete") is True and entry.get("status") == "complete"):
            file_year = int(entry.get("year", -1))
            start = str(entry.get("coverage_start", ""))
            end = str(entry.get("coverage_end", ""))
            if start.startswith(f"{file_year}-01-01") and end.startswith(f"{file_year + 1}-01-01"):
                completed.add(file_year)
    return {year - 1, year, year + 1}.issubset(completed)


def _prepare(detections: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    df = detections.copy()
    required = {"country", "stream", "type"}
    missing = sorted(required - set(df.columns))
    if missing:
        return pd.DataFrame(columns=[*required, "weekday", "year", "daynight"]), {
            "rows_input": len(df), "rows_used": 0, "missing_columns": missing}
    date_col = "local_date" if "local_date" in df else "local" if "local" in df else None
    if date_col is None:
        return pd.DataFrame(columns=[*required, "weekday", "year", "daynight"]), {
            "rows_input": len(df), "rows_used": 0, "missing_columns": ["local_date or local"]}
    # Do not reconstruct civil dates from UTC or trust an externally computed weekday.
    dates = pd.to_datetime(df[date_col], errors="coerce")
    invalid = dates.isna()
    df["year"] = dates.dt.year
    df["weekday"] = dates.dt.day_of_week
    df["type"] = pd.to_numeric(df["type"], errors="coerce")
    known = df["country"].isin(REST_DAYS) & df["stream"].isin(STREAMS)
    df = df[~invalid & known].copy()
    if "daynight" not in df:
        df["daynight"] = "?"
    else:
        df["daynight"] = df["daynight"].astype(str).str.upper()
    return df, {"rows_input": int(len(detections)), "rows_used": int(len(df)),
                "invalid_local_dates": int(invalid.sum()), "unknown_country_or_stream": int((~known).sum()),
                "unknown_fire_types": int((~df["type"].isin([0, 1, 2, 3])).sum()), "missing_columns": []}


def analyse_stream(sub: pd.DataFrame, country: str, stream: str, subset: str,
                   manifest: dict, config: dict, control: bool = False) -> dict:
    years, exploratory, excluded = [], [], []
    verified, exploratory_years = [], []
    used_detections = 0
    for raw_year, group in sub.groupby("year", sort=True):
        year = int(raw_year)
        if year >= config["as_of_year"] or len(group) < config["min_detections_per_year"]:
            excluded.append({"year": year, "detections": len(group), "reason": "incomplete current/future year or low count"})
            continue
        counts = np.bincount(group["weekday"].astype(int), minlength=7).astype(float)
        rate = counts / weekday_exposure(year)
        index = rate / rate.mean()
        if verified_local_year(manifest, country, stream, year):
            years.append(index)
            verified.append(year)
            used_detections += len(group)
        else:
            exploratory.append(index)
            exploratory_years.append(year)
    result = {"country": country, "stream": stream, "subset": subset,
              "rest_day": REST_DAYS[country], "status": "insufficient_data",
              "years": len(verified), "year_list": verified, "detections": int(len(sub)),
              "detections_used": int(used_detections), "period_verified": True,
              "unverified_years": exploratory_years, "excluded_years": excluded,
              "weekdays": [], "p_null": None, "p_adjusted": None,
              "rest_is_lowest": False, "ci_upper_below_one": False, "significant": False}
    # Unverified estimates remain inspectable but NEVER satisfy the release gate.
    if len(years) < config["min_years"]:
        if len(years) + len(exploratory) < config["min_years"]:
            result["reason"] = "Fewer than the required years of detections."
            return result
        years = years + exploratory
        result.update(period_verified=False, years=len(years),
                      year_list=sorted(verified + exploratory_years),
                      reason="Exploratory estimate: input-period completeness is unverified.")
    else:
        result["status"] = "ok"
        result["reason"] = "Annual archive coverage verified; actual observing exposure remains unknown."
    Y = np.asarray(years)
    n = len(Y)
    rng = _rng(config["seed"], f"{country}|{stream}|{subset}|{control}|{result['year_list']}")
    boots = Y[rng.integers(0, n, (config["bootstrap_draws"], n))].mean(axis=1)
    random_days = rng.integers(0, 7, (config["null_draws"], n))
    null = Y[np.arange(n)[None, :], random_days].mean(axis=1)
    mean = Y.mean(axis=0)
    lo, hi = np.percentile(boots, [2.5, 97.5], axis=0)
    r = DAYS.index(REST_DAYS[country])
    p = float((np.count_nonzero(null <= mean[r]) + 1) / (len(null) + 1))
    # Fixed, predefined country × stream family; unavailable tests are not dropped.
    m = len(REST_DAYS) * len(STREAMS)
    p_adj = min(p * m, 1.0)
    lowest = bool(mean[r] == mean.min())
    result.update(weekdays=[{"day": d, "index": float(mean[i]), "lo": float(lo[i]), "hi": float(hi[i])}
                            for i, d in enumerate(DAYS)],
                  p_null=p, p_adjusted=p_adj, bonferroni_m=m,
                  lowest_day=DAYS[int(mean.argmin())], rest_index=float(mean[r]),
                  rest_is_lowest=lowest, ci_upper_below_one=bool(hi[r] < 1),
                  significant=bool(result["status"] == "ok" and lowest and hi[r] < 1
                                   and p_adj < config["alpha"]))
    return result


def analyse_family(df: pd.DataFrame, manifest: dict, config: dict, subset: str = "all",
                   control: bool = False) -> list[dict]:
    frame = df[df["type"].isin([1, 2])] if control else df[df["type"] == 0]
    if subset == "day":
        frame = frame[frame["daynight"] == "D"]
    return [analyse_stream(frame[(frame.country == country) & (frame.stream == stream)],
                           country, stream, subset, manifest, config, control)
            for country in REST_DAYS for stream in STREAMS]


def make_gate(main: list[dict], controls: list[dict], label: str) -> dict:
    """Stricter re-analysis used ONLY as robustness checks, never as the official gate."""
    per_country = {}
    for country in REST_DAYS:
        rows = [r for r in main if r["country"] == country]
        valid = [r for r in rows if r["status"] == "ok"]
        positive = [r for r in valid if r["significant"]]
        status = "insufficient_data" if len(valid) < 2 else "pass" if len(positive) >= 2 else "fail"
        country_controls = [r for r in controls if r["country"] == country and r["status"] == "ok"]
        # Require matched controls for the streams used to make a country claim.
        matched_controls = [r for r in country_controls if r["stream"] in {v["stream"] for v in positive}]
        control_status = ("insufficient_data" if len(matched_controls) < 2 else
                          "flagged" if any(r["significant"] for r in matched_controls) else "no_detected_rest_day_dip")
        per_country[country] = {"status": status, "streams_with_data": len(valid),
                                "streams_significant": len(positive), "rest_day": REST_DAYS[country],
                                "controls_status": control_status}
    us = per_country["United_States"]
    others = [c for c, row in per_country.items() if c != "United_States" and row["status"] == "pass"]
    available = [c for c, row in per_country.items() if c != "United_States" and row["status"] != "insufficient_data"]
    if us["status"] == "insufficient_data" or len(available) < 2:
        statistical = "insufficient_data"
    elif us["status"] == "pass" and len(others) >= 2:
        statistical = "pass"
    else:
        statistical = "fail"
    qualified = [c for c in others if per_country[c]["controls_status"] == "no_detected_rest_day_dip"]
    decision = statistical
    reasons = []
    if statistical == "pass":
        if us["controls_status"] == "flagged":
            decision = "fail"
            reasons.append("US diagnostic control has a corrected rest-day dip; investigate before release.")
        elif us["controls_status"] != "no_detected_rest_day_dip" or len(qualified) < 2:
            decision = "insufficient_data"
            reasons.append("Not enough matching, unflagged control results for US plus two other countries.")
    synthetic = "SYNTHETIC" in label.upper() or "FAKE" in label.upper() or "MOCK" in label.upper()
    if synthetic:
        decision = "insufficient_data"
        reasons.append("Synthetic data verify software behavior and cannot enable a real-data scientific claim.")
    if statistical == "insufficient_data":
        reasons.append("Need at least five verified years in two streams for the US and two other countries.")
    if statistical == "fail":
        reasons.append("The predefined US-plus-two-country statistical criterion was not met.")
    return {"decision": decision, "statistical_decision": statistical,
            "production_allowed": decision == "pass" and not synthetic,
            "label": label, "countries_passing": others, "qualified_countries": qualified,
            "per_country": per_country, "replication_check": {"country": "United_States", "status": us["status"]},
            "reasons": reasons, "caveats": CAVEATS,
            "rule": "US and >=2 other countries each require >=2 streams with verified input years, rest day lowest, 95% upper bound <1 and fixed-family adjusted p<0.05; matching controls must be available and unflagged. Synthetic data never enable production."}


OFFICIAL_SOURCE = "kill_test.py (pre-registered gate; reference/kill_test.py)"
ROBUSTNESS_DESCRIPTIONS = {
    "ci_upper_below_one": "Rest-day 95% upper bound below 1.0 in at least two streams (official estimates).",
    "strict_reanalysis": "Re-analysis using only years with both neighbouring annual archives, rest day lowest, "
                         "95% upper bound below 1 and fixed 21-test Bonferroni, in at least two streams.",
    "matched_static_controls": "At least two per-country static-source control streams available, none showing "
                               "a corrected rest-day dip.",
}
SYNTHETIC_WORDS = ("SYNTHETIC", "FAKE", "MOCK")


def load_official(directory) -> dict | None:
    """Read the official pre-registered gate and per-stream estimates written by kill_test.py."""
    folder = Path(directory)
    gate_path, results_path = folder / "kill_test_gate.json", folder / "kill_test_results.csv"
    if not gate_path.exists() or not results_path.exists():
        return None
    return {"gate": json.loads(gate_path.read_text(encoding="utf-8")), "results": pd.read_csv(results_path)}


def official_gate(official: dict | None, label: str) -> dict:
    """The published decision. Comes only from kill_test.py; synthetic input never enables it."""
    if official is None:
        return {"decision": "insufficient_data", "source": OFFICIAL_SOURCE, "label": label,
                "reasons": ["Official pre-registered gate (kill_test.py outputs) was not supplied."]}
    gate = dict(official["gate"])
    labels = (label + " " + str(gate.get("label", ""))).upper()
    if any(word in labels for word in SYNTHETIC_WORDS):
        return {"decision": "insufficient_data", "source": OFFICIAL_SOURCE, "label": label,
                "reasons": ["Synthetic data cannot enable a real-data scientific claim."]}
    gate.pop("negative_control_static_sources", None)
    gate["source"] = OFFICIAL_SOURCE
    return gate


def robustness_checks(official: dict | None, strict: dict, controls: list[dict] | None = None) -> dict:
    """Per officially passing country: which stricter checks hold. Reported, never gating."""
    checks = {}
    gate = (official or {}).get("gate", {})
    results = (official or {}).get("results")
    for country, row in gate.get("per_country", {}).items():
        if row.get("status") != "pass":
            continue
        rest = row.get("predicted_rest_day") or REST_DAYS.get(country)
        n_ci = 0
        if results is not None and f"{rest}_hi" in results:
            sub = results[(results.country == country) & (results.subset == "all") & (results.status == "ok")]
            n_ci = int((sub[f"{rest}_hi"] < 1).sum())
        strict_row = strict.get("per_country", {}).get(country, {})
        country_checks = {
            "ci_upper_below_one": {"passed": n_ci >= 2, "streams": n_ci},
            "strict_reanalysis": {"passed": strict_row.get("status") == "pass",
                                  "status": strict_row.get("status", "not_run"),
                                  "streams_significant": strict_row.get("streams_significant", 0)},
            "matched_static_controls": {"passed": strict_row.get("controls_status") == "no_detected_rest_day_dip",
                                        "status": strict_row.get("controls_status", "not_run")},
        }
        flagged = [{"stream": c["stream"], "rest_day": c.get("rest_day"), "rest_index": c.get("rest_index"),
                    "p_adjusted": c.get("p_adjusted"), "years": c.get("years"),
                    "first_year": (c.get("year_list") or [None])[0], "last_year": (c.get("year_list") or [None])[-1]}
                   for c in (controls or []) if c.get("country") == country and c.get("significant")]
        country_checks["matched_static_controls"]["flagged_streams"] = flagged
        failed = [name for name, value in country_checks.items() if not value["passed"]]
        checks[country] = {**country_checks, "failed": failed, "all_passed": not failed}
    return {"role": "robustness checks reported next to the official decision; they never change it",
            "descriptions": ROBUSTNESS_DESCRIPTIONS, "per_country": checks,
            "strict_variant": {"decision": strict.get("decision"), "per_country": strict.get("per_country"),
                               "rule": strict.get("rule"), "reasons": strict.get("reasons")}}


def robustness_from_saved(official_dir, strict_results_path, output_dir=None) -> dict:
    """Robustness checks from an existing strict run (e.g. the seven-country streaming release).

    The saved rhythm_results.json supplies the strict gate and per-country controls; nothing is re-estimated.
    """
    saved = json.loads(Path(strict_results_path).read_text(encoding="utf-8"))
    strict = (saved.get("robustness") or {}).get("strict_variant") or saved["gate"]
    official = load_official(official_dir)
    result = robustness_checks(official, strict, saved.get("controls"))
    result["strict_source"] = str(strict_results_path).replace("\\", "/")
    if output_dir:
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        (Path(output_dir) / "robustness_checks.json").write_text(json.dumps(result, indent=2, allow_nan=False),
                                                                  encoding="utf-8")
    return result


def _plot(rows: list[dict], output: Path, label: str) -> str:
    """Always emit an inspectable SVG; optionally also PNG if matplotlib exists."""
    visible = [r for r in rows if r["weekdays"]]
    width, row_height = 1000, 190
    height = max(200, 90 + len(visible) * row_height)
    svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
           '<rect width="100%" height="100%" fill="#faf8f2"/>',
           f'<text x="28" y="32" font-size="22" font-family="sans-serif">{html.escape(label)} — weekly detection patterns</text>',
           '<text x="28" y="56" font-size="13" font-family="sans-serif">Index 1 = annual weekday-rate average. Whiskers: 95% year-bootstrap intervals. Separate streams.</text>']
    if not visible:
        svg.append('<text x="28" y="120" font-size="20" font-family="sans-serif">Insufficient data: no eligible weekday estimates.</text>')
    for j, row in enumerate(visible):
        y0 = 90 + j * row_height
        values = row["weekdays"]
        maximum = max(1.25, max(v["hi"] for v in values))
        scale = 108 / maximum
        baseline = y0 + 140
        svg.append(f'<text x="28" y="{y0}" font-size="15" font-family="sans-serif">{html.escape(row["country"])} / {row["stream"]} / {row["years"]} years / {row["status"]}</text>')
        svg.append(f'<line x1="28" x2="950" y1="{baseline-scale}" y2="{baseline-scale}" stroke="#777" stroke-dasharray="4 4"/>')
        for i, val in enumerate(values):
            x = 50 + i * 128
            h = val["index"] * scale
            color = "#c74424" if val["day"] == row["rest_day"] else "#557570"
            svg.append(f'<rect x="{x}" y="{baseline-h:.2f}" width="72" height="{h:.2f}" fill="{color}"/>')
            top, bottom = baseline - val["hi"] * scale, baseline - val["lo"] * scale
            svg.extend([f'<line x1="{x+36}" x2="{x+36}" y1="{top:.2f}" y2="{bottom:.2f}" stroke="#222"/>',
                        f'<text x="{x+16}" y="{baseline+20}" font-size="13" font-family="sans-serif">{val["day"]}</text>'])
    svg.append('</svg>')
    (output / "rhythm.svg").write_text("\n".join(svg), encoding="utf-8")
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        return "rhythm.svg"
    fig, axes = plt.subplots(max(1, len(visible)), 1, figsize=(11, max(3, len(visible) * 2.0)), squeeze=False)
    if not visible:
        axes[0][0].text(.5, .5, "Insufficient data", ha="center")
        axes[0][0].set_axis_off()
    for ax, row in zip(axes[:, 0], visible):
        vals = np.array([v["index"] for v in row["weekdays"]])
        low = np.array([v["lo"] for v in row["weekdays"]])
        high = np.array([v["hi"] for v in row["weekdays"]])
        # Draw interval endpoints directly: a percentile interval need not contain the point estimate.
        ax.bar(DAYS, vals, color=["#c74424" if d == row["rest_day"] else "#557570" for d in DAYS])
        ax.vlines(np.arange(7), low, high, color="#222")
        ax.axhline(1, color="#444", lw=.7, ls="--")
        ax.set_title(f'{row["country"]} / {row["stream"]} / {row["years"]} years / {row["status"]}', fontsize=10)
        ax.set_ylabel("Rate index")
    fig.suptitle(label + " — weekly detection patterns")
    fig.tight_layout(rect=(0, 0, 1, .98))
    fig.savefig(output / "rhythm.png", dpi=110)
    plt.close(fig)
    return "rhythm.png"


def run(detections: pd.DataFrame, output_dir, label: str = "REAL FIRMS DATA", manifest=None,
        config: dict | None = None, official=None) -> dict:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    settings = {**DEFAULTS, **(config or {})}
    manifest = _manifest_dict(manifest if manifest is not None else detections.attrs.get("manifest"))
    # Data provenance overrides an accidentally omitted synthetic label.
    source_label = str(detections.attrs.get("label", manifest.get("label", "")))
    if any(word in source_label.upper() for word in ("SYNTHETIC", "FAKE", "MOCK")):
        label = source_label
    df, diagnostics = _prepare(detections)
    main = analyse_family(df, manifest, settings)
    daytime = analyse_family(df, manifest, settings, subset="day")
    controls = analyse_family(df, manifest, settings, control=True)
    strict = make_gate(main, controls, label)
    official_data = load_official(official) if isinstance(official, (str, Path)) else official
    gate = official_gate(official_data, label)
    robustness = robustness_checks(official_data if gate.get("decision") != "insufficient_data" else None, strict,
                                   controls)
    diagnostics.update(label=label, settings=settings, observation_coverage="unknown",
                       archive_manifest_supplied=bool(manifest),
                       main_family_tests=len(REST_DAYS) * len(STREAMS),
                       daytime_family="separate exploratory sensitivity analysis; not used by gate",
                       control_family="separate diagnostic family; no dip is not proof of equivalence")
    countries = {country: {"rest_day": rest, "streams": [r for r in main if r["country"] == country],
                           "daytime_streams": [r for r in daytime if r["country"] == country],
                           "status": gate.get("per_country", {}).get(country, {}).get("status", "insufficient_data"),
                           "strict_status": strict["per_country"][country]["status"]}
                 for country, rest in REST_DAYS.items()}
    result = {"gate": gate, "robustness": robustness, "countries": countries, "diagnostics": diagnostics,
              "controls": controls}
    for name, payload in [("kill_test_gate.json", gate), ("robustness_checks.json", robustness),
                          ("kill_test_diagnostics.json", diagnostics), ("rhythm_results.json", result)]:
        (output / name).write_text(json.dumps(payload, indent=2, allow_nan=False), encoding="utf-8")
    flat = []
    for family, rows in [("vegetation_all", main), ("vegetation_day", daytime), ("static_control", controls)]:
        for row in rows:
            entry = {k: v for k, v in row.items() if k not in {"weekdays", "year_list", "unverified_years", "excluded_years"}}
            entry.update(label=label, family=family, year_list=",".join(map(str, row["year_list"])))
            for day in row["weekdays"]:
                entry.update({day["day"]: day["index"], day["day"] + "_lo": day["lo"], day["day"] + "_hi": day["hi"]})
            flat.append(entry)
    pd.DataFrame(flat).to_csv(output / "kill_test_results.csv", index=False)
    diagnostics["figure"] = _plot(main, output, label)
    (output / "kill_test_diagnostics.json").write_text(json.dumps(diagnostics, indent=2), encoding="utf-8")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("detections", nargs="?", help="Cleaned parquet or CSV with local civil dates")
    parser.add_argument("--from-saved", help="Strict rhythm_results.json to derive robustness checks from, "
                                             "without re-estimating anything")
    parser.add_argument("--manifest")
    parser.add_argument("--output", default="reports")
    parser.add_argument("--label", default="REAL FIRMS DATA")
    parser.add_argument("--official", help="Folder with kill_test.py outputs (the official gate)")
    args = parser.parse_args()
    if args.from_saved:
        if not args.official:
            parser.error("--from-saved needs --official")
        checks = robustness_from_saved(args.official, args.from_saved, args.output)
        print(json.dumps({c: v["failed"] for c, v in checks["per_country"].items()}, indent=2))
        raise SystemExit(0)
    if not args.detections:
        parser.error("detections is required unless --from-saved is used")
    path = Path(args.detections)
    data = pd.read_parquet(path) if path.suffix == ".parquet" else pd.read_csv(path)
    result = run(data, args.output, args.label, args.manifest, official=args.official)
    print(json.dumps({"official_decision": result["gate"].get("decision"),
                      "robustness": result["robustness"]["per_country"]}, indent=2, default=str))
