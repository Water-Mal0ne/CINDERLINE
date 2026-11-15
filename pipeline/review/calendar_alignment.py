"""Derive an additive, source-bound annual globe view matching daily exclusions.

Original globe, national/daily payloads, model and evaluation remain read-only.
Every affected grid cell is derived from exact, pre-cleaned local-date counts;
the 84 published daily cells are verification targets, never a spatial proxy.
"""
from __future__ import annotations

import argparse
import calendar
from collections import defaultdict
import hashlib
import json
import math
from pathlib import Path
import struct

import pandas as pd

from pipeline.globe import manifest_fingerprint
from pipeline.streaming.estimate_dictionary import decode_table
from pipeline.streaming.prepare_analysis import input_snapshot

ROOT = Path(__file__).resolve().parents[2]
REVISION = "calendar-dates-v1"
ROUNDING_TOLERANCE = 366 * 0.000005 + 1e-8


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def globe_view_hash(globe):
    """Portable binary identity: years, archive identity, ordered IDs and values."""
    digest = hashlib.sha256(b"calendar-alignment-v1\0")
    digest.update(struct.pack("<I", len(globe["years"])))
    for year in globe["years"]:
        digest.update(struct.pack("<I", year))
    digest.update(globe["archive_manifest_fingerprint"].encode() + b"\0")
    for cell in globe["cells"]:
        digest.update(cell["id"].encode() + b"\0")
        for value in cell["values"]:
            if value is not None and (not math.isfinite(value) or value < 0):
                raise ValueError("Globe contains a nonfinite/negative value")
            digest.update(struct.pack("<Bd", 0 if value is None else 1, 0.0 if value is None else value))
    return digest.hexdigest()


def daily_rows(path):
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    table = payload.get("daily_compact", payload)
    if "columns" in table:
        return payload, [dict(zip(table["columns"], row)) for row in decode_table(table)]
    if isinstance(payload.get("daily"), list):
        return payload, payload["daily"]
    raise ValueError(f"No supported daily table in {path}")


def published_masks(public, globe):
    masks, national, inputs = {}, {}, []
    years = set(globe["years"])
    for region in globe["coverage_regions"]:
        country = region["id"]
        path = Path(public) / f"{country}.json"
        payload, rows = daily_rows(path)
        rows = [r for r in rows if r.get("cell_id") == "ALL" and int(r["date"][:4]) in years]
        if len({r["date"] for r in rows}) != len(rows):
            raise ValueError(f"Duplicate national local dates: {country}")
        mask = set()
        for row in rows:
            if row["source"] == "no observation":
                if row["harmonized"] is not None:
                    raise ValueError(f"Excluded date has a value: {country}/{row['date']}")
                mask.add(row["date"])
        masks[country] = mask
        national[country] = (payload, rows)
        inputs.append({"file": f"{country}.json", "sha256": sha256(path)})
    if not masks or len({tuple(sorted(dates)) for dates in masks.values()}) != 1:
        raise ValueError("This compact revision requires the same exclusion dates in every country")
    return masks, national, inputs


def correction_values(frame, masks, source_by_year, model):
    """Return exact source counts removed from each cell/year, using local dates."""
    if frame.empty:
        return {}, 0
    f = frame[frame.type == 0].copy()
    dates = pd.to_datetime(f.local_date)
    if not (dates.dt.year.to_numpy() == f.year.to_numpy()).all():
        raise ValueError("Prepared year disagrees with local date")
    f["date"] = dates.dt.strftime("%Y-%m-%d")
    keep = [date in masks.get(country, set()) and stream == source_by_year.get((country, int(year)))
            for country, date, stream, year in zip(f.country, f.date, f.stream, f.year)]
    f = f.loc[keep].copy()
    if f.empty:
        return {}, 0
    if (f.n < 0).any() or not (f.n % 1 == 0).all():
        raise ValueError("Prepared multiplicities must be nonnegative integers")
    result = defaultdict(int)
    for row in f.itertuples():
        result[(row.country, row.cell_id, int(row.year), row.stream, row.stratum)] += int(row.n)
    return dict(result), int(f.n.sum())


def encode_corrections(counts, globe, model):
    index = {cell["id"]: i for i, cell in enumerate(globe["cells"])}
    if len(index) != len(globe["cells"]):
        raise ValueError("Duplicate annual cell IDs")
    totals = defaultdict(list)
    for (country, cell, year, stream, stratum), count in counts.items():
        if stream == "Aqua":
            value = float(count)
        else:
            selected = model["selection"][country]["selected"]
            ratios = model["ratios"]
            factor = ratios["B1"] if selected == "B1" else ratios["M1"].get(f"{country}|{stratum}", ratios["B1"])
            value = count * factor
        totals[(f"{country}:{cell}", year)].append(value)
    values, dictionary, corrections = [], {}, defaultdict(list)
    for (cell_id, year), pieces in sorted(totals.items()):
        removed = math.fsum(pieces)
        if removed == 0:
            continue
        if cell_id not in index or year not in globe["years"]:
            raise ValueError(f"Correction references absent globe cell/year: {cell_id}/{year}")
        ci, yi = index[cell_id], globe["years"].index(year)
        original = globe["cells"][ci]["values"][yi]
        if original is None or removed < 0 or removed > original + 1e-8:
            raise ValueError(f"Invalid subtraction: {cell_id}/{year}")
        key = removed.hex()
        if key not in dictionary:
            dictionary[key] = len(values)
            values.append(removed)
        corrections[str(year)].append([ci, dictionary[key]])
    return values, {year: sorted(rows) for year, rows in sorted(corrections.items())}


def aligned_values(globe, payload):
    values = [list(cell["values"]) for cell in globe["cells"]]
    for year, rows in payload["corrections"].items():
        yi = globe["years"].index(int(year))
        for ci, di in rows:
            values[ci][yi] = max(0.0, values[ci][yi] - payload["deductions"][di])
    for year, coverage in payload["coverage"].items():
        if coverage["retained_dates"] == 0:
            yi = globe["years"].index(int(year))
            for row in values:
                row[yi] = None
    return values


def reconcile(public, globe, payload, national):
    values = aligned_values(globe, payload)
    by_id = {cell["id"]: i for i, cell in enumerate(globe["cells"])}
    national_errors, cell_errors, checked = [], [], 0
    for country, (meta, rows) in national.items():
        for year in globe["years"]:
            yi = globe["years"].index(year)
            expected = math.fsum(float(r["harmonized"]) for r in rows if r["date"].startswith(str(year)) and r["harmonized"] is not None)
            actual = math.fsum(v[yi] for cell, v in zip(globe["cells"], values) if cell["region"] == country and v[yi] is not None)
            national_errors.append(abs(actual - expected))
        for cell in meta["cells"]:
            file = Path(public) / cell["file"]
            if not file.exists():
                file = Path(public) / "cells" / Path(cell["file"]).name
            _, daily = daily_rows(file)
            ci = by_id[f"{country}:{cell['id']}"]
            for yi, year in enumerate(globe["years"]):
                expected = math.fsum(float(r["harmonized"]) for r in daily if r["date"].startswith(str(year)) and r["harmonized"] is not None)
                actual = values[ci][yi]
                if actual is None:
                    raise ValueError("Unexpected unavailable annual value in published cell")
                cell_errors.append(abs(actual - expected))
                checked += 1
    if max(national_errors + cell_errors, default=0) > ROUNDING_TOLERANCE:
        raise ValueError(f"Daily/annual reconciliation failed: national {max(national_errors)}, cell {max(cell_errors)}")
    return {"national_country_years": len(national_errors), "published_cell_years": checked,
            "max_national_absolute_difference": max(national_errors), "max_cell_absolute_difference": max(cell_errors),
            "daily_rounding_absolute_tolerance": ROUNDING_TOLERANCE}


def build(public, model_path, preparations, output, report_dir):
    public, model_path, output, report_dir = map(Path, (public, model_path, output, report_dir))
    globe_path = public / "globe.json"
    globe = json.loads(globe_path.read_text())
    model = json.loads(model_path.read_text())
    source_hash, model_hash = sha256(globe_path), sha256(model_path)
    manifest, all_paths = input_snapshot(preparations)
    fingerprint = manifest_fingerprint(manifest)
    if fingerprint != globe["archive_manifest_fingerprint"] or fingerprint != model["archive_manifest_fingerprint"]:
        raise ValueError("Count sources, locked model and original globe have different archive identities")
    masks, national, national_inputs = published_masks(public, globe)
    sources = {(r["id"], y): "VIIRS" if s == "converted VIIRS" else "Aqua" if s == "observed Aqua" else None
               for r in globe["coverage_regions"] for y, s in zip(globe["years"], r["sources"])}
    excluded = sorted(next(iter(masks.values())))
    # Adjacent UTC archives may contain local dates on either side of New Year.
    mask_years = {int(d[:4]) for d in excluded}
    count_inputs, counts, removed_detections = [], defaultdict(int), 0
    for path in sorted(all_paths):
        if int(path.parent.name) not in {y + offset for y in mask_years for offset in (-1, 0, 1)}:
            continue
        country = path.parent.parent.parent.name
        if not any(sources.get((country, y)) == ("VIIRS" if path.parent.parent.name == "viirs-snpp" else "Aqua") for y in mask_years):
            continue
        frame = pd.read_parquet(path)
        part, n = correction_values(frame, masks, sources, model)
        for key, value in part.items():
            counts[key] += value
        removed_detections += n
        count_inputs.append({"file": path.as_posix().split("/archives/", 1)[1], "sha256": sha256(path)})
    deductions, corrections = encode_corrections(counts, globe, model)
    coverage = {}
    for year in globe["years"]:
        dates = [d for d in excluded if d.startswith(str(year))]
        total = 366 if calendar.isleap(year) else 365
        coverage[str(year)] = {"calendar_dates": total, "excluded_dates": dates, "retained_dates": total - len(dates)}
    payload = {"revision": REVISION, "encoding": "indexed-deduction-dictionary-v1", "years": globe["years"],
               "countries": [r["id"] for r in globe["coverage_regions"]], "cell_count": len(globe["cells"]),
               "source": {"globe_sha256": source_hash, "globe_view_sha256": globe_view_hash(globe), "model_sha256": model_hash,
                          "archive_manifest_fingerprint": fingerprint},
               "scope": "All annual grid cells; same excluded local dates as published daily calendar values.",
               "coverage_note": "Retained dates are unmasked calendar dates, not measured clear-sky observation exposure. Partial-year totals are not extrapolated.",
               "area_monthly_note": "Area monthly data omit whole outage-affected months and round each cell-month to tenths; their totals use a different support than this daily-aligned annual view.",
               "coverage": coverage, "deductions": deductions, "corrections": corrections}
    result = reconcile(public, globe, payload, national)
    if sha256(globe_path) != source_hash or sha256(model_path) != model_hash or any(sha256(public / r["file"]) != r["sha256"] for r in national_inputs):
        raise ValueError("An input changed during generation; rerun against a stable snapshot")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, separators=(",", ":"), allow_nan=False), encoding="utf-8")
    report = {"revision": REVISION, "artifact_sha256": sha256(output), "artifact_bytes": output.stat().st_size,
              "source": payload["source"], "national_inputs": national_inputs, "count_partitions": count_inputs,
              "excluded_recorded_detections": removed_detections, "corrected_cell_years": sum(map(len, corrections.values())),
              "deduction_dictionary_size": len(deductions), "reconciliation": result}
    report_dir.mkdir(parents=True, exist_ok=True)
    (report_dir / "alignment-build.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--preparations", nargs="+", required=True)
    ap.add_argument("--public", type=Path, default=ROOT / "web/public/data")
    ap.add_argument("--model", type=Path, default=ROOT / "reports/harmonization_model.json")
    ap.add_argument("--output", type=Path, default=ROOT / "web/public/data/calendar-alignment.json")
    ap.add_argument("--report-dir", type=Path, default=ROOT / "reports/calendar-confidence")
    args = ap.parse_args()
    report = build(args.public, args.model, args.preparations, args.output, args.report_dir)
    print(json.dumps({k: v for k, v in report.items() if k not in ("count_partitions", "national_inputs")}, indent=2))


if __name__ == "__main__":
    main()
