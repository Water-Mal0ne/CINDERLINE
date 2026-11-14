"""Build the standalone human-rhythm web payload from the OFFICIAL kill_test.py outputs.

python -m pipeline.rhythm_web [--official reports/official] [--robustness reports/rhythm_robustness]
                              [--output web/public/data]

Every number in web/public/data/rhythm.json is copied from files written by scripts in this
repository (reference/kill_test.py, pipeline/rhythm.py, reference/rhythm_map.py); nothing is
computed or typed in here except grouping and the data-driven Sunday caveat.
"""
from __future__ import annotations

import argparse
import json
import math
import shutil
from pathlib import Path

import pandas as pd

from pipeline.rhythm import DAYS, REST_DAYS

NAMES = {"United_States": "United States", "Australia": "Australia", "Brazil": "Brazil", "India": "India",
         "Nepal": "Nepal", "Bangladesh": "Bangladesh", "Egypt": "Egypt"}
STREAMS = ["Terra", "Aqua", "VIIRS"]
DAY_NAMES = {"Mon": "Monday", "Tue": "Tuesday", "Wed": "Wednesday", "Thu": "Thursday", "Fri": "Friday",
             "Sat": "Saturday", "Sun": "Sunday"}
SHORT = {"United_States": "the US"}
SUNDAY_CAVEAT = ("All three passing countries rest on Sunday; Friday- and Saturday-rest countries did not show "
                 "a dip, so this does not show the dip following each country's own rest day.")


def _num(value):
    try:
        value = float(value)
    except (TypeError, ValueError):
        return None
    return None if math.isnan(value) else round(value, 4)


def _streams(results: pd.DataFrame, country: str, subset: str) -> list[dict]:
    out = []
    for stream in STREAMS:
        rows = results[(results.country == country) & (results.subset == subset) & (results.stream == stream)]
        if rows.empty:
            continue
        r = rows.iloc[0]
        entry = {"stream": stream, "status": r.status, "detections": int(r.detections)}
        if r.status == "ok":
            entry.update(years=int(r.years), rest_index=_num(r.rest_index), lowest_day=r.lowest_day,
                         rest_is_lowest=bool(r.rest_is_lowest), p_null=_num(r.p_null),
                         bonferroni_m=int(r.bonferroni_m), significant=bool(r.significant),
                         weekdays=[{"day": d, "index": _num(r[d]), "lo": _num(r[f"{d}_lo"]),
                                    "hi": _num(r[f"{d}_hi"])} for d in DAYS])
        out.append(entry)
    return out


def _join(items):
    return items[0] if len(items) == 1 else ", ".join(items[:-1]) + " and " + items[-1]


def control_notes(robustness: dict | None, comparison: dict | None, decision: str) -> dict:
    """Plain-language note for each passing country whose matched static control is flagged."""
    notes = {}
    per_country = (robustness or {}).get("per_country", {})
    clean = [c for c, v in per_country.items() if v["matched_static_controls"]["passed"]]
    for country, value in per_country.items():
        flagged = value["matched_static_controls"].get("flagged_streams") or []
        if not flagged:
            continue
        name = NAMES.get(country, country)
        parts = [f"{f['stream']} static-source control also dips on {DAY_NAMES.get(f['rest_day'], f['rest_day'])} "
                 f"(index {f['rest_index']:.3f}, adjusted p = {f['p_adjusted']:.3f})" for f in flagged]
        text = (f"{name}'s {' and '.join(parts)}, so {name}'s vegetation-fire dip cannot be cleanly separated from "
                f"weekly patterns in industrial heat sources.")
        earlier = ((comparison or {}).get("per_country", {}).get(country, {}) or {}).get("matched_static_controls", {})
        years = (comparison or {}).get("years")
        if earlier.get("passed") and years:
            text += f" The control was clean on {years}."
        others = [SHORT.get(c, NAMES.get(c, c)) for c in clean]
        text += f" The official pre-specified result is unchanged ({decision.upper()})"
        text += f", but {name}'s support is weaker than {_join(others)}." if others else "."
        notes[country] = text
    return notes


def control_nuance(robustness: dict | None) -> str | None:
    per_country = (robustness or {}).get("per_country", {})
    clean = [SHORT.get(c, NAMES.get(c, c)) for c, v in per_country.items() if v["matched_static_controls"]["passed"]]
    if not any(not v["matched_static_controls"]["passed"] for v in per_country.values()):
        return None
    text = ("A Sunday dip in static sources does not by itself mean a satellite artifact: some type-2 static sources "
            "are industrial sites that may also follow the work week.")
    if clean:
        text += (f" The clean static controls in {_join(clean)} are what argue against a satellite or processing "
                 f"artifact.")
    return text


WEB_CELL_FIELDS = ["country", "cell_lat", "cell_lon", "rest_day", "years", "mean_detections_per_year", "rest_index",
                   "ci_lo", "ci_hi", "q_bh", "significant", "aqua_rest_index", "aqua_significant"]


def write_compact_cells(source, target):
    """Web copy of the per-cell map as a column table (fields the panel shows, 3-decimal rounding).
    Each cell is the 1x1 degree square whose south-west corner is (cell_lat, cell_lon). The full GeoJSON,
    with polygons and all fields, stays in reports/official/rhythm_cells.geojson."""
    full = json.loads(Path(source).read_text(encoding="utf-8"))
    def keep(value):
        return round(value, 3) if isinstance(value, float) else value
    rows = [[keep(f["properties"].get(k)) for k in WEB_CELL_FIELDS] for f in full["features"]]
    compact = {"metadata": full.get("metadata", {}), "source": "reports/official/rhythm_cells.geojson",
               "columns": WEB_CELL_FIELDS, "rows": rows}
    Path(target).write_text(json.dumps(compact, separators=(",", ":"), allow_nan=False), encoding="utf-8")


def build(official_dir, robustness_dir, output_dir, comparison_dir=None) -> dict:
    official_dir, output_dir = Path(official_dir), Path(output_dir)
    gate = json.loads((official_dir / "kill_test_gate.json").read_text(encoding="utf-8"))
    results = pd.read_csv(official_dir / "kill_test_results.csv")
    missing = [f"{d}_{k}" for d in DAYS for k in ("lo", "hi") if f"{d}_{k}" not in results]
    if missing:
        raise ValueError(f"kill_test_results.csv lacks per-day CI columns {missing[:2]}...; rerun kill_test.py")
    diagnostics_path = official_dir / "kill_test_diagnostics.json"
    diagnostics = json.loads(diagnostics_path.read_text(encoding="utf-8")) if diagnostics_path.exists() else {}
    robustness_path = Path(robustness_dir) / "robustness_checks.json" if robustness_dir else None
    robustness = json.loads(robustness_path.read_text(encoding="utf-8")) \
        if robustness_path and robustness_path.exists() else None

    comparison_path = Path(comparison_dir) / "robustness_checks.json" if comparison_dir else None
    comparison = json.loads(comparison_path.read_text(encoding="utf-8")) \
        if comparison_path and comparison_path.exists() else None
    if comparison is not None:
        meta = Path(comparison_dir) / "years.txt"
        comparison["years"] = meta.read_text(encoding="utf-8").strip() if meta.exists() else None

    per_country = gate.get("per_country", {})
    passing = [c for c, v in per_country.items() if v.get("status") == "pass"]
    non_sunday = [c for c in per_country if REST_DAYS.get(c) != "Sun"]
    caveats = list(gate.get("caveats", []))
    sunday_only = bool(passing) and all(REST_DAYS.get(c) == "Sun" for c in passing) and \
        not any(per_country[c].get("status") == "pass" for c in non_sunday)
    flagged = {c: v["failed"] for c, v in (robustness or {}).get("per_country", {}).items() if v.get("failed")}
    payload = {
        "label": gate.get("label", "UNVERIFIED INPUT"),
        "official": {"decision": gate.get("decision"), "rule": gate.get("rule"),
                     "source": "kill_test.py (pre-specified gate; reference/kill_test.py)",
                     "replication_check": gate.get("replication_check"),
                     "countries_passing": gate.get("countries_passing", []),
                     "per_country": per_country},
        "sunday_caveat": SUNDAY_CAVEAT if sunday_only else None,
        "robustness": robustness and {"role": robustness.get("role"), "descriptions": robustness.get("descriptions"),
                                      "per_country": robustness.get("per_country"), "flagged": flagged,
                                      "source": robustness.get("strict_source"),
                                      "notes": control_notes(robustness, comparison, str(gate.get("decision"))),
                                      "control_nuance": control_nuance(robustness)},
        "countries": [{"country": c, "name": NAMES.get(c, c), "rest_day": REST_DAYS[c],
                       "status": per_country.get(c, {}).get("status", "insufficient_data"),
                       "streams": _streams(results, c, "all"), "daytime_streams": _streams(results, c, "day")}
                      for c in REST_DAYS if c in per_country],
        "negative_control": gate.get("negative_control_static_sources", []),
        "diagnostics": {k: diagnostics.get(k) for k in ("files", "rows_loaded", "rows_vegetation",
                                                        "rows_static_control", "vegetation") if k in diagnostics},
        "caveats": caveats,
        "wording": "A rest-day dip is consistent with people scheduling their burning. It is not proof of cause, "
                   "and no dip does not mean fires are weather-driven. Counts are satellite detections, not fires.",
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "rhythm.json").write_text(json.dumps(payload, indent=1, allow_nan=False), encoding="utf-8")
    cells = official_dir / "rhythm_cells.geojson"
    if cells.exists():
        write_compact_cells(cells, output_dir / "rhythm_cells.json")
        stale = output_dir / "rhythm_cells.geojson"
        if stale.exists():
            stale.unlink()
    summary = official_dir / "rhythm_summary.json"
    if summary.exists():
        shutil.copyfile(summary, output_dir / "rhythm_cells_summary.json")
    return payload


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--official", default="reports/official")
    parser.add_argument("--robustness", default="reports/rhythm_robustness")
    parser.add_argument("--output", default="web/public/data")
    parser.add_argument("--compare", default="reports/rhythm_robustness_2014_2023",
                        help="Earlier robustness run, used only to say whether a flagged control was clean there")
    args = parser.parse_args()
    payload = build(args.official, args.robustness, args.output, args.compare)
    print(json.dumps({"decision": payload["official"]["decision"],
                      "passing": payload["official"]["countries_passing"],
                      "sunday_caveat": bool(payload["sunday_caveat"]),
                      "robustness_flagged": (payload["robustness"] or {}).get("flagged"),
                      "notes": (payload["robustness"] or {}).get("notes")}, indent=2))


if __name__ == "__main__":
    main()
