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


def build(official_dir, robustness_dir, output_dir) -> dict:
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
                     "source": "kill_test.py (pre-registered gate; reference/kill_test.py)",
                     "replication_check": gate.get("replication_check"),
                     "countries_passing": gate.get("countries_passing", []),
                     "per_country": per_country},
        "sunday_caveat": SUNDAY_CAVEAT if sunday_only else None,
        "robustness": robustness and {"role": robustness.get("role"), "descriptions": robustness.get("descriptions"),
                                      "per_country": robustness.get("per_country"), "flagged": flagged},
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
        shutil.copyfile(cells, output_dir / "rhythm_cells.geojson")
    summary = official_dir / "rhythm_summary.json"
    if summary.exists():
        shutil.copyfile(summary, output_dir / "rhythm_cells_summary.json")
    return payload


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--official", default="reports/official")
    parser.add_argument("--robustness", default="reports/rhythm_robustness")
    parser.add_argument("--output", default="web/public/data")
    args = parser.parse_args()
    payload = build(args.official, args.robustness, args.output)
    print(json.dumps({"decision": payload["official"]["decision"],
                      "passing": payload["official"]["countries_passing"],
                      "sunday_caveat": bool(payload["sunday_caveat"]),
                      "robustness_flagged": (payload["robustness"] or {}).get("flagged")}, indent=2))


if __name__ == "__main__":
    main()
