"""Download canonical FIRMS annual country archives with resumable, audited transfers."""
from __future__ import annotations
import argparse
import concurrent.futures
import csv
import hashlib
import json
import os
from pathlib import Path
import time
import urllib.request

BASE = "https://firms.modaps.eosdis.nasa.gov/data/country"
COUNTRIES = ["United_States", "Nepal", "Bangladesh", "Egypt", "Australia", "India", "Brazil"]
SENSORS = ["modis", "viirs-snpp"]


def _inspect(path):
    with path.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.reader(f)
        header = next(reader, [])
        required = {"latitude", "longitude", "acq_date", "acq_time", "satellite", "confidence"}
        if not required.issubset(header):
            raise ValueError(f"Not a FIRMS CSV: header {header[:8]}")
        rows = sum(1 for _ in reader)
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(block)
    return rows, digest.hexdigest()


def _fetch(country, year, sensor, data_dir):
    name = f"{sensor}_{year}_{country}.csv"
    path = Path(data_dir) / sensor / str(year) / name
    url = f"{BASE}/{sensor}/{year}/{name}"
    result = dict(country=country, year=int(year), sensor=sensor, url=url,
                  path=str(path.resolve()), status="failed", complete=False,
                  coverage_start=f"{year}-01-01T00:00:00Z", coverage_end=f"{year+1}-01-01T00:00:00Z",
                  completeness_basis="Canonical annual archive transferred and CSV validated; satellite coverage unknown")
    path.parent.mkdir(parents=True, exist_ok=True)
    part = path.with_suffix(".csv.part")
    try:
        if not path.exists() or path.stat().st_size == 0:
            for attempt in range(3):
                try:
                    request = urllib.request.Request(url, headers={"User-Agent": "CINDERLINE-research/0.1"})
                    with urllib.request.urlopen(request, timeout=90) as source, part.open("wb") as target:
                        expected = int(source.headers.get("Content-Length", "0"))
                        while chunk := source.read(1024 * 1024):
                            target.write(chunk)
                    if expected and part.stat().st_size != expected:
                        raise ValueError("Transfer length mismatch")
                    _inspect(part)
                    os.replace(part, path)
                    break
                except Exception:
                    part.unlink(missing_ok=True)
                    if attempt == 2:
                        raise
                    time.sleep(attempt + 1)
        rows, digest = _inspect(path)
        result.update(status="complete", complete=True, rows=rows, sha256=digest, bytes=path.stat().st_size)
    except Exception as error:
        result["error"] = f"{type(error).__name__}: {error}"
    print(f"{country} {sensor} {year}: {result['status']} ({result.get('rows', 0):,} rows)", flush=True)
    return result


def download(countries, years, sensors=SENSORS, data_dir="data/raw", workers=4):
    data_dir = Path(data_dir)
    data_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = data_dir / "manifest.json"
    old = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else {"files": []}
    records = {(r["country"], r["sensor"], r["year"]): r for r in old["files"]}
    tasks = [(c, int(y), s) for c in countries for y in years for s in sensors if not (s == "viirs-snpp" and y < 2012)]
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {executor.submit(_fetch, c, y, s, data_dir): (c, s, y) for c, y, s in tasks}
        for future in concurrent.futures.as_completed(futures):
            result = future.result()
            records[(result["country"], result["sensor"], result["year"])] = result
            manifest = {"label": "REAL FIRMS DATA", "source": BASE, "files": list(records.values()),
                        "observation_coverage": "unknown", "note": "Complete annual archive is not complete satellite observation coverage."}
            tmp = manifest_path.with_suffix(".tmp")
            tmp.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
            os.replace(tmp, manifest_path)
    return manifest


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--countries", nargs="+", default=["Nepal", "United_States"])
    p.add_argument("--years", nargs=2, type=int, default=[2012, 2025], metavar=("START", "END"))
    p.add_argument("--sensors", nargs="+", choices=SENSORS, default=SENSORS)
    p.add_argument("--data-dir", default="data/raw")
    p.add_argument("--workers", type=int, default=4)
    args = p.parse_args()
    manifest = download(args.countries, range(args.years[0], args.years[1] + 1), args.sensors, args.data_dir, args.workers)
    failures = [r for r in manifest["files"] if not r["complete"]]
    print(f"Manifest: {args.data_dir}/manifest.json; incomplete files: {len(failures)}")
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
