"""Publish a compact view of the verified, retrospective season comparison.

Run: python -m pipeline.review.season_payload
Uses the existing independently checked daily inputs; no refitting or new study.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from collections import defaultdict
from datetime import date
from pathlib import Path

SERIES = ("Aqua", "raw", "B1", "selected")
MASKS = ("primary", "padded")
YEARS = tuple(range(2020, 2025))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read_csv(path):
    with Path(path).open(encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


def metrics(months, column):
    reference = [r[1] for r in months]
    values = [r[column] for r in months]
    a, b = math.fsum(reference), math.fsum(values)
    supported = all(r[0] > 0 for r in months)
    error = abs(b - a) / a if a > 0 else None
    tv = 0.5 * math.fsum(abs(x / a - y / b) for x, y in zip(reference, values)) if supported and a > 0 and b > 0 else None
    return error, tv


def build(source):
    source = Path(source)
    receipt = json.loads((source / "verification/independent_verification.json").read_text())
    if receipt.get("status") != "PASS":
        raise ValueError("Season study has no passing independent verification receipt")
    required = ("daily_inputs.csv", "excluded_dates.csv", "whole_year_comparison.csv", "input_manifest.json")
    hashes = {name: sha(source / name) for name in required}
    if any(receipt["verified_output_sha256"].get(name) != digest for name, digest in hashes.items()):
        raise ValueError("Season source differs from the independently verified outputs")
    manifest = json.loads((source / "input_manifest.json").read_text())
    if manifest["years"] != list(YEARS):
        raise ValueError("Unexpected research years")
    countries = manifest["countries"]
    excluded = {mask: set() for mask in MASKS}
    for row in read_csv(source / "excluded_dates.csv"):
        if row["mask"] in excluded:
            excluded[row["mask"]].add(row["date"])
    if [len(excluded[m]) for m in MASKS] != [73, 87]:
        raise ValueError("Frozen common-date masks changed")
    grouped = defaultdict(list)
    identities = set()
    for row in read_csv(source / "daily_inputs.csv"):
        d = date.fromisoformat(row["date"])
        country = row["country"]
        if country not in countries or d.year not in YEARS or int(row["year"]) != d.year:
            raise ValueError("Unexpected country or year")
        identity = country, d
        if identity in identities:
            raise ValueError("Duplicate daily input")
        identities.add(identity)
        values = tuple(float(row[s]) for s in SERIES)
        if any(not math.isfinite(v) or v < 0 for v in values):
            raise ValueError("Invalid daily values")
        for mask in MASKS:
            if row["date"] not in excluded[mask]:
                grouped[country, mask, d.year, d.month].append(values)
    result = {}
    for country in countries:
        model = manifest["selected_models"][country]
        if model not in {"B1", "M1"}:
            raise ValueError("Unsupported frozen model")
        result[country] = {"model": model, "masks": {}}
        for mask in MASKS:
            frames = []
            for year in YEARS:
                expected = (date(year + 1, 1, 1) - date(year, 1, 1)).days
                if sum(c == country and d.year == year for c, d in identities) != expected:
                    raise ValueError("Daily input year is incomplete")
                months = []
                for month in range(1, 13):
                    rows = grouped[country, mask, year, month]
                    if not rows:
                        raise ValueError("A month has no retained observation dates")
                    months.append([len(rows), *[round(math.fsum(row[i] for row in rows), 9) for i in range(4)]])
                frames.append({"year": year, "months": months})
            result[country]["masks"][mask] = frames
    # Independent monthly accumulation must reproduce every reported whole-year mean.
    checked = 0
    for row in read_csv(source / "whole_year_comparison.csv"):
        if row["mask"] not in MASKS:
            continue
        frames = result[row["country"]]["masks"][row["mask"]]
        column = SERIES.index(row["alternative"]) + 1
        values = [metrics(f["months"], column) for f in frames]
        for index, key in ((0, "mean_abs_annual_error"), (1, "mean_tv")):
            actual = math.fsum(v[index] for v in values) / len(values)
            if not math.isclose(actual, float(row[key]), rel_tol=1e-9, abs_tol=1e-10):
                raise ValueError(f"Published seasonal summary mismatch: {row['country']} {row['mask']} {key}")
            checked += 1
    if checked != len(countries) * 2 * 3 * 2:
        raise ValueError("Incomplete reference summary")
    return {"version": 1, "years": list(YEARS), "columns": ["retained_days", *SERIES],
            "mask_days": {m: len(excluded[m]) for m in MASKS}, "countries": result,
            "provenance": {"source": "reports/review/season", "verified_inputs": hashes,
                           "receipt_sha256": sha(source / "verification/independent_verification.json"),
                           "input_sha256": manifest["input_sha256"], "checked_summary_values": checked,
                           "scope": "Retrospective national whole-year replacement controls; frozen models; Aqua reference, not ground truth",
                           "rounding": "Monthly sums rounded to 9 decimal places; published summaries checked within 1e-9 relative / 1e-10 absolute tolerance"}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=Path("reports/review/season"))
    parser.add_argument("--output", type=Path, default=Path("web/public/data/season-comparison.json"))
    parser.add_argument("--check", action="store_true", help="Check the existing payload without writing")
    args = parser.parse_args()
    payload = build(args.source)
    encoded = (json.dumps(payload, separators=(",", ":"), allow_nan=False) + "\n").encode()
    if args.check:
        if args.output.read_bytes() != encoded:
            raise ValueError("Published seasonal payload is stale")
    else:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_bytes(encoded)
    print(f"Season payload verified: {len(encoded)} bytes; {payload['provenance']['checked_summary_values']} reference metrics checked")


if __name__ == "__main__":
    main()
