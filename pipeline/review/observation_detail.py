"""Export source-coordinate VIIRS observations, separate from harmonized estimates.

The observed layer uses UTC acquisition dates and retains qualifying archived
records on dates excluded from the local-date harmonized calendar. It neither
refits nor applies calibration, fills gaps, deduplicates passes, or subdivides
coarse harmonized counts. All source coordinates remain at archive precision.
"""
from __future__ import annotations

import argparse
import calendar
from collections import Counter
from decimal import Decimal, ROUND_FLOOR
import hashlib
import json
from pathlib import Path
import time

import numpy as np
import pandas as pd

from pipeline.clean import _utc_datetime
from pipeline.review.no_observation import OUTAGES

SCHEMA = "observations-v1"
YEAR = 2024
SENSOR = "VIIRS S-NPP"
GRID_SIZE = 0.05
TILE_SIZE = 2
MAX_TILE_ROWS = 8_000
COUNTRIES = ["Australia", "Bangladesh", "Brazil", "Egypt", "India", "Nepal", "United_States"]
COLUMNS = ["lat", "lon", "utc", "confidence", "scan", "track", "frp", "daynight"]
CALENDAR_POLICY = (
    "UTC acquisition dates; qualifying archived observations are retained on dates "
    "excluded from the harmonized calendar. Calendar dates are local civil dates "
    "and use different outage handling. These raw counts are not directly comparable "
    "with harmonized calendar or annual globe totals."
)
COVERAGE_NOTE = (
    "A date or area with no qualifying records does not establish no fire or complete "
    "satellite coverage. Cloud, overpass and detection coverage remain unknown. "
    "Repeated observations are detections, not distinct fires."
)


def sha256(path: Path) -> str:
    result = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            result.update(block)
    return result.hexdigest()


def _write(path: Path, value: dict) -> tuple[str, int]:
    data = json.dumps(value, ensure_ascii=False, allow_nan=False, separators=(",", ":")).encode("utf-8")
    if len(data) > 25 * 1024 * 1024:
        raise ValueError(f"Payload exceeds the 25 MiB asset limit: {path.name}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return hashlib.sha256(data).hexdigest(), len(data)


def coordinate_index(value: float, size: float) -> int:
    """Decimal floor avoids binary division shifting exact grid boundaries."""
    return int((Decimal(str(value)) / Decimal(str(size))).to_integral_value(rounding=ROUND_FLOOR))


def _optional_numeric(series: pd.Series, *, positive: bool = False) -> pd.Series:
    values = pd.to_numeric(series, errors="coerce")
    valid = np.isfinite(values) & (values > 0 if positive else values >= 0)
    return values.where(valid)


def clean_observations(raw: pd.DataFrame, year: int = YEAR) -> tuple[pd.DataFrame, dict]:
    """Apply archived vegetation/quality/time filters without changing positions.

    This reuses the main pipeline's timestamp parser and nominal/high confidence
    rule. The archive is explicitly S-NPP; unexpected satellite rows are rejected
    rather than accidentally mixing VIIRS platforms. Civil-time conversion is
    intentionally absent because this layer is labelled UTC acquisition dates.
    """
    required = {"latitude", "longitude", "acq_date", "acq_time", "satellite", "confidence", "type"}
    if not required.issubset(raw.columns):
        raise ValueError(f"Missing observation fields: {sorted(required - set(raw.columns))}")
    confidence = raw.confidence.astype(str).str.strip().str.lower()
    satellite = raw.satellite.astype(str).str.strip().str.upper()
    quality = confidence.isin(["n", "h", "nominal", "high"])
    source = satellite.isin(["N", "SUOMI-NPP", "S-NPP"])
    vegetation = pd.to_numeric(raw.type, errors="coerce").eq(0)
    utc = _utc_datetime(raw)
    lat = pd.to_numeric(raw.latitude, errors="coerce")
    lon = pd.to_numeric(raw.longitude, errors="coerce")
    coords = lat.between(-90, 90) & lon.between(-180, 180)
    date_ok = utc.notna() & utc.dt.year.eq(year)
    keep = source & quality & vegetation & coords & date_ok
    result = pd.DataFrame({
        "lat": lat, "lon": lon, "utc": utc,
        "confidence": confidence.replace({"nominal": "n", "high": "h"}),
        "scan": _optional_numeric(raw.get("scan", pd.Series(np.nan, index=raw.index)), positive=True),
        "track": _optional_numeric(raw.get("track", pd.Series(np.nan, index=raw.index)), positive=True),
        "frp": _optional_numeric(raw.get("frp", pd.Series(np.nan, index=raw.index))),
        "daynight": raw.get("daynight", pd.Series("?", index=raw.index)).fillna("?").astype(str).str.upper(),
    }).loc[keep].copy()
    result.loc[~result.daynight.isin(["D", "N"]), "daynight"] = "?"
    diagnostics = {
        "raw_rows": int(len(raw)), "retained_rows": int(keep.sum()),
        "unexpected_satellite": int((~source).sum()),
        "excluded_confidence": int((~quality).sum()),
        "non_vegetation_or_unknown_type": int((~vegetation).sum()),
        "invalid_coordinates": int((~coords).sum()),
        "invalid_or_outside_year_timestamp": int((~date_ok).sum()),
        "unknown_frp_retained": int(result.frp.isna().sum()),
        "unknown_footprint_retained": int((result.scan.isna() | result.track.isna()).sum()),
    }
    return result, diagnostics


def _rows(frame: pd.DataFrame) -> list[list]:
    result = []
    for row in frame[COLUMNS].itertuples(index=False, name=None):
        lat, lon, utc, confidence, scan, track, frp, daynight = row
        result.append([
            float(lat), float(lon), utc.strftime("%Y-%m-%dT%H:%M:00Z"), confidence,
            float(scan) if pd.notna(scan) else None,
            float(track) if pd.notna(track) else None,
            float(frp) if pd.notna(frp) else None, daynight,
        ])
    return result


def spatial_parts(frame: pd.DataFrame, bounds: list[float], tile_id: str,
                  max_tile_rows: int, depth: int = 0):
    """Split dense storage tiles spatially so close zoom can reduce download size.

    Repeated identical coordinates cannot be separated spatially. Only those
    irreducible groups (or extremely tiny cells) are split into same-bounds parts;
    every part remains listed so consumers never silently sample observations.
    """
    west, south, east, north = bounds
    coincident = frame.lat.nunique() == 1 and frame.lon.nunique() == 1
    if len(frame) <= max_tile_rows or coincident or depth >= 12:
        for part, start in enumerate(range(0, len(frame), max_tile_rows)):
            yield f"{tile_id}_{part}", bounds, frame.iloc[start:start + max_tile_rows]
        return
    mid_lon, mid_lat = (west + east) / 2, (south + north) / 2
    quadrants = (frame.lat.ge(mid_lat).astype(int) * 2 + frame.lon.ge(mid_lon).astype(int))
    for quadrant, group in frame.groupby(quadrants, sort=True):
        upper, right = int(quadrant) // 2, int(quadrant) % 2
        child_bounds = [mid_lon if right else west, mid_lat if upper else south,
                        east if right else mid_lon, north if upper else mid_lat]
        yield from spatial_parts(group, child_bounds, f"{tile_id}q{quadrant}", max_tile_rows, depth + 1)


def export_month(frame: pd.DataFrame, country: str, month: str, output: Path,
                 source_sha256: str, max_tile_rows: int = MAX_TILE_ROWS) -> dict:
    if max_tile_rows < 1:
        raise ValueError("max_tile_rows must be positive")
    frame = frame.sort_values(["lat", "lon", "utc"], kind="stable").copy()
    grid_counts = Counter((min(1799, coordinate_index(a, GRID_SIZE)), min(3599, coordinate_index(b, GRID_SIZE)))
                          for a, b in zip(frame.lat, frame.lon))
    grid = [[a, b, int(n)] for (a, b), n in sorted(grid_counts.items())]
    # Exact +90/+180 coordinates belong to the final in-range grid/storage cell;
    # the original point coordinates themselves are unchanged.
    frame["tile_lat"] = [min(44, coordinate_index(a, TILE_SIZE)) for a in frame.lat]
    frame["tile_lon"] = [min(89, coordinate_index(b, TILE_SIZE)) for b in frame.lon]
    tiles = []
    for (lat_index, lon_index), group in frame.groupby(["tile_lat", "tile_lon"], sort=True):
        south, west = int(lat_index) * TILE_SIZE, int(lon_index) * TILE_SIZE
        tile_bounds = [west, south, west + TILE_SIZE, south + TILE_SIZE]
        for tile_id, bounds, chunk in spatial_parts(group, tile_bounds, f"{int(lat_index)}_{int(lon_index)}", max_tile_rows):
            relative = f"{country}/{month}/{tile_id}.json"
            payload = {
                "schema": SCHEMA, "sensor": SENSOR, "country": country, "month": month,
                "id": tile_id, "time_basis": "UTC", "columns": COLUMNS,
                "count": len(chunk), "bounds": bounds, "rows": _rows(chunk),
            }
            digest, size = _write(output / relative, payload)
            tiles.append({"id": tile_id, "file": f"observations/{relative}", "sha256": digest,
                          "count": len(chunk), "bounds": bounds, "bytes": size})
    year, month_number = map(int, month.split("-"))
    days = pd.date_range(f"{month}-01", periods=calendar.monthrange(year, month_number)[1]).strftime("%Y-%m-%d")
    counts = frame.utc.dt.strftime("%Y-%m-%d").value_counts().to_dict()
    daily_counts = [[date, int(counts.get(date, 0))] for date in days]
    payload = {
        "schema": SCHEMA, "sensor": SENSOR, "country": country, "month": month,
        "time_basis": "UTC", "grid_size": GRID_SIZE, "count": len(frame),
        "source_sha256": source_sha256, "grid": grid, "tiles": tiles,
        "daily_counts": daily_counts,
        "zero_record_dates": [date for date, n in daily_counts if not n],
    }
    if sum(row[2] for row in grid) != len(frame) or sum(t["count"] for t in tiles) != len(frame):
        raise ValueError("Count conservation failed")
    relative = f"{country}/{month}.json"
    digest, size = _write(output / relative, payload)
    return {"month": month, "file": f"observations/{relative}", "sha256": digest,
            "count": len(frame), "bytes": size, "tile_count": len(tiles)}


def build(manifest_path: Path, output: Path, *, countries: list[str] | None = None,
          chunk_rows: int = 200_000, max_tile_rows: int = MAX_TILE_ROWS) -> tuple[dict, dict]:
    started = time.monotonic()
    countries = COUNTRIES if countries is None else countries
    if len(set(countries)) != len(countries) or set(countries) - set(COUNTRIES):
        raise ValueError("Unknown or duplicate country")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    records = [r for r in manifest["files"] if r["sensor"] == "viirs-snpp" and int(r["year"]) == YEAR
               and r["country"] in countries]
    if Counter(r["country"] for r in records) != Counter(countries):
        raise ValueError("Require exactly one 2024 VIIRS S-NPP source archive per country")
    index = {
        "schema": SCHEMA, "sensor": SENSOR, "year": YEAR, "time_basis": "UTC",
        "temporal_precision": "minute", "grid_size": GRID_SIZE, "tile_size": TILE_SIZE,
        "columns": COLUMNS, "nominal_resolution_m": 375,
        "calendar_policy": CALENDAR_POLICY, "coverage_note": COVERAGE_NOTE,
        "position_note": "Coordinates are satellite pixel centres, not exact fire locations or fire boundaries. Scan/track describe reported pixel dimensions in kilometres; orientation is not supplied.",
        "quality_policy": "Presumed vegetation fires (type 0), nominal/high confidence, valid S-NPP source, coordinates and UTC acquisition timestamps. No calibration, interpolation or deduplication of repeated observations.",
        "known_outages": [{"start": start, "end": end, "reason": reason}
                          for stream, start, end, reason in OUTAGES if stream == "VIIRS" and start.startswith(str(YEAR))],
        "outage_note": "Notice dates give context for possible gaps. This observed-record view retains qualifying archived records and does not apply the harmonized calendar's local-date outage exclusions.",
        "countries": [],
    }
    receipt = {"schema": SCHEMA, "source_manifest_sha256": sha256(manifest_path), "countries": []}
    for country in countries:
        record = next(r for r in records if r["country"] == country)
        source = Path(record["path"])
        if not record.get("complete") or record.get("status") not in {"complete", "ok"}:
            raise ValueError(f"Archive is not declared complete: {country}")
        if sha256(source) != record["sha256"]:
            raise ValueError(f"Source hash mismatch: {country}")
        pieces, diagnostics = [], Counter()
        for raw in pd.read_csv(source, chunksize=chunk_rows, low_memory=False):
            clean, stats = clean_observations(raw)
            diagnostics.update(stats)
            pieces.append(clean)
        if diagnostics["raw_rows"] != int(record["rows"]):
            raise ValueError(f"Source row count mismatch: {country}")
        frame = pd.concat(pieces, ignore_index=True) if pieces else clean_observations(pd.DataFrame(columns=["latitude", "longitude", "acq_date", "acq_time", "satellite", "confidence", "type"]))[0]
        frame["month"] = frame.utc.dt.strftime("%Y-%m")
        months = [export_month(frame.loc[frame.month == f"{YEAR}-{m:02d}"], country, f"{YEAR}-{m:02d}",
                               output, record["sha256"], max_tile_rows) for m in range(1, 13)]
        if sum(m["count"] for m in months) != diagnostics["retained_rows"]:
            raise ValueError(f"Monthly count conservation failed: {country}")
        country_entry = {"id": country, "name": country.replace("_", " "),
                         "source": {"url": record["url"], "sha256": record["sha256"], "rows": int(record["rows"])},
                         "count": int(len(frame)), "months": months}
        index["countries"].append(country_entry)
        receipt["countries"].append({"id": country, "source_sha256": record["sha256"],
                                     "diagnostics": dict(diagnostics), "count": len(frame),
                                     "tiles": sum(m["tile_count"] for m in months)})
        print(f"{country}: {len(frame):,} observations; {sum(m['tile_count'] for m in months):,} tiles", flush=True)
    digest, _ = _write(output / "index.json", index)
    files = list(output.rglob("*.json"))
    if len(files) > 19_000:
        raise ValueError("Observation exports leave insufficient room under the Pages 20,000-file cap")
    receipt.update(index_sha256=digest, files=len(files), bytes=sum(p.stat().st_size for p in files),
                   largest_file_bytes=max(p.stat().st_size for p in files), seconds=round(time.monotonic() - started, 3),
                   total_detections=sum(c["count"] for c in index["countries"]))
    return index, receipt


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=Path("reports/data_manifest.json"))
    parser.add_argument("--output", type=Path, default=Path("web/public/data/observations"))
    parser.add_argument("--receipt", type=Path, default=Path("reports/observation-detail/generation.json"))
    args = parser.parse_args()
    if args.output.exists() and any(args.output.iterdir()):
        raise SystemExit("Use a fresh export directory; existing artifacts are preserved.")
    _, receipt = build(args.manifest, args.output)
    args.receipt.parent.mkdir(parents=True, exist_ok=True)
    args.receipt.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in receipt.items() if k != "countries"}, indent=2))


if __name__ == "__main__":
    main()
