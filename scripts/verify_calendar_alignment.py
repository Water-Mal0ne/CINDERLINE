"""Independent full-grid and daily-table check; imports no alignment implementation.

Reaccumulate declared source partitions, independently apply frozen ratios, compare
every sparse correction, then reconcile all published national and daily cells.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
from datetime import date
import hashlib
import json
import math
from pathlib import Path
import struct

import pandas as pd


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read_daily(path):
    p = json.loads(Path(path).read_text())
    t = p.get("daily_compact", p)
    if "rows" not in t:
        return p, p["daily"]
    rows = []
    for r in t["rows"]:
        rows.append({c: t["dictionaries"][c][r[i]] if c in t.get("dictionaries", {}) else r[i]
                     for i, c in enumerate(t["columns"])})
    return p, rows


def verify(public, model_path, preparations, artifact, build_report):
    public = Path(public)
    model = json.loads(Path(model_path).read_text())
    globe = json.loads((public / "globe.json").read_text())
    overlay = json.loads(Path(artifact).read_text())
    receipt = json.loads(Path(build_report).read_text())
    assert overlay["source"]["globe_sha256"] == digest(public / "globe.json"), "Globe source changed"
    assert overlay["source"]["model_sha256"] == digest(model_path), "Frozen model changed"
    assert receipt["artifact_sha256"] == digest(artifact), "Artifact differs from build receipt"
    assert overlay["years"] == globe["years"] and overlay["cell_count"] == len(globe["cells"])
    years, masks, national = set(globe["years"]), {}, {}
    for region in globe["coverage_regions"]:
        country = region["id"]
        p, rows = read_daily(public / (country + ".json"))
        rows = [r for r in rows if r["cell_id"] == "ALL" and int(r["date"][:4]) in years]
        national[country] = (p, rows)
        masks[country] = {r["date"] for r in rows if r["source"] == "no observation"}
        assert all(r["harmonized"] is None for r in rows if r["date"] in masks[country])
        assert len(rows) == len({r["date"] for r in rows})
    mask = next(iter(masks.values()))
    assert all(m == mask for m in masks.values())
    for year in globe["years"]:
        days = (date(year + 1, 1, 1) - date(year, 1, 1)).days
        removed_dates = sorted(d for d in mask if d.startswith(str(year)))
        assert overlay["coverage"][str(year)] == {"calendar_dates": days, "excluded_dates": removed_dates, "retained_dates": days - len(removed_dates)}
    # Verify binary identity independently of the producer's streaming implementation.
    content = [b"calendar-alignment-v1\0", struct.pack("<I", len(globe["years"]))]
    content += [struct.pack("<I", y) for y in globe["years"]]
    content += [(globe["archive_manifest_fingerprint"] + "\0").encode()]
    for cell in globe["cells"]:
        content.append((cell["id"] + "\0").encode())
        content.extend(struct.pack("<Bd", v is not None, v or 0.0) for v in cell["values"])
    assert hashlib.sha256(b"".join(content)).hexdigest() == overlay["source"]["globe_view_sha256"]
    del content
    # Read only declared partitions; directory globbing could admit stale cache files.
    archived, paths, declarations = [], [], set()
    for folder in map(Path, preparations):
        prep = json.loads((folder / "PREPARATION.json").read_text())
        manifest = json.loads((folder / "source_manifest.json").read_text())
        archived.extend(manifest["files"])
        source = {(r["country"], r["sensor"], r["year"]): r for r in manifest["files"]}
        for a in prep["archives"]:
            key = (a["country"], a["sensor"], a["year"])
            assert key not in declarations, "Duplicate archive"
            declarations.add(key)
            assert source[key]["complete"] and source[key]["sha256"] == a["signature"]["source_sha256"]
            for name in a["outputs"]:
                if Path(name).name.startswith("counts-"):
                    paths.append(folder / name)
    records = [{k: r.get(k) for k in ("country", "sensor", "year", "sha256", "complete", "status")} for r in archived]
    records.sort(key=lambda r: (str(r["country"]), str(r["sensor"]), int(r["year"] or 0)))
    fingerprint = hashlib.sha256(json.dumps(records, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    assert fingerprint == globe["archive_manifest_fingerprint"] == model["archive_manifest_fingerprint"]
    sources = {(r["id"], y): ("VIIRS" if s == "converted VIIRS" else "Aqua" if s == "observed Aqua" else None)
               for r in globe["coverage_regions"] for y, s in zip(globe["years"], r["sources"])}
    source_years = {int(d[:4]) + offset for d in mask for offset in (-1, 0, 1)}
    contributions, input_hashes, raw_removed = defaultdict(list), {}, 0
    for path in paths:
        if int(path.parent.name) not in source_years:
            continue
        country, sensor = path.parent.parent.parent.name, path.parent.parent.name
        expected_stream = "VIIRS" if sensor == "viirs-snpp" else "Aqua"
        if not any(sources.get((country, int(d[:4]))) == expected_stream for d in masks[country]):
            continue
        frame = pd.read_parquet(path)
        local_dates = pd.to_datetime(frame.local_date).dt.strftime("%Y-%m-%d")
        frame = frame[(frame.type == 0) & local_dates.isin(masks[country])].copy()
        frame["date"] = pd.to_datetime(frame.local_date).dt.strftime("%Y-%m-%d")
        for row in frame.itertuples():
            year = int(row.date[:4])
            assert year == row.year and row.country == country
            if row.stream != sources.get((country, year)):
                continue
            n = int(row.n)
            assert n >= 0 and n == row.n
            if row.stream == "Aqua":
                factor = 1.0
            elif model["selection"][country]["selected"] == "B1":
                factor = float(model["ratios"]["B1"])
            else:
                factor = float(model["ratios"]["M1"].get(country + "|" + row.stratum, model["ratios"]["B1"]))
            contributions[(country + ":" + row.cell_id, year)].append(n * factor)
            raw_removed += n
        input_hashes[path.as_posix().split("/archives/", 1)[1]] = digest(path)
    assert input_hashes == {r["file"]: r["sha256"] for r in receipt["count_partitions"]}
    expected = {k: math.fsum(v) for k, v in contributions.items() if math.fsum(v) > 0}
    supplied = {}
    values = [list(c["values"]) for c in globe["cells"]]
    for year, rows in overlay["corrections"].items():
        yi = globe["years"].index(int(year))
        for ci, di in rows:
            assert 0 <= ci < len(globe["cells"]) and 0 <= di < len(overlay["deductions"])
            key = (globe["cells"][ci]["id"], int(year))
            assert key not in supplied, "Repeated cell/year correction"
            removed = overlay["deductions"][di]
            assert removed > 0 and math.isfinite(removed) and values[ci][yi] is not None and removed <= values[ci][yi] + 1e-8
            supplied[key] = removed
            values[ci][yi] = max(0.0, values[ci][yi] - removed)
    assert set(supplied) == set(expected), "Correction footprint differs from full-grid source"
    for key in expected:
        assert math.isclose(expected[key], supplied[key], rel_tol=1e-12, abs_tol=1e-9), key
    ids = {c["id"]: i for i, c in enumerate(globe["cells"])}
    national_errors, cell_errors = [], []
    for country, (p, daily) in national.items():
        sums = defaultdict(list)
        for row in daily:
            if row["harmonized"] is not None:
                sums[int(row["date"][:4])].append(row["harmonized"])
        for yi, year in enumerate(globe["years"]):
            total = math.fsum(values[i][yi] for i, c in enumerate(globe["cells"]) if c["region"] == country and values[i][yi] is not None)
            national_errors.append(abs(total - math.fsum(sums[year])))
        for cell in p["cells"]:
            _, rows = read_daily(public / cell["file"])
            cell_years = defaultdict(list)
            for r in rows:
                if r["harmonized"] is not None:
                    cell_years[int(r["date"][:4])].append(r["harmonized"])
            ci = ids[country + ":" + cell["id"]]
            for yi, year in enumerate(globe["years"]):
                cell_errors.append(abs(values[ci][yi] - math.fsum(cell_years[year])))
    tolerance = 366 * 0.5e-5 + 1e-8
    assert max(national_errors + cell_errors) <= tolerance
    assert raw_removed == receipt["excluded_recorded_detections"]
    return {"status": "PASS", "method": "Independent declared-partition accumulation, frozen ratio application and published daily-table decoding; no producer imports.",
            "artifact_sha256": digest(artifact), "model_sha256": digest(model_path), "original_globe_sha256": digest(public / "globe.json"),
            "source_partitions_checked": len(input_hashes), "full_grid_corrected_cell_years": len(expected),
            "excluded_recorded_detections": raw_removed, "national_country_years": len(national_errors),
            "published_cell_years": len(cell_errors), "max_national_absolute_difference": max(national_errors),
            "max_cell_absolute_difference": max(cell_errors), "daily_rounding_absolute_tolerance": tolerance,
            "scope": "2003-2024 daily-aligned annual grid; not AOI whole-month totals or proof of cloud-free observations."}


def main():
    root = Path(__file__).resolve().parents[1]
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--preparations", nargs="+", required=True)
    ap.add_argument("--public", type=Path, default=root / "web/public/data")
    ap.add_argument("--model", type=Path, default=root / "reports/harmonization_model.json")
    ap.add_argument("--artifact", type=Path, default=root / "web/public/data/calendar-alignment.json")
    ap.add_argument("--build-report", type=Path, default=root / "reports/calendar-confidence/alignment-build.json")
    ap.add_argument("--output", type=Path, default=root / "reports/calendar-confidence/alignment-verification.json")
    args = ap.parse_args()
    result = verify(args.public, args.model, args.preparations, args.artifact, args.build_report)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
