"""Resume the three additional-country archives without changing production inputs."""
from __future__ import annotations
import argparse
import concurrent.futures
import json
import os
from pathlib import Path
import shutil
import sys
import threading
import time
import urllib.request

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from pipeline.download import BASE, _inspect
from .aggregate_archives import write_json

LOCK = threading.Lock()
STOP = threading.Event()


def fetch(country, year, sensor, directory, reserve):
    name = f"{sensor}_{year}_{country}.csv"
    path = directory / sensor / str(year) / name
    part = path.with_suffix(".csv.part")
    url = f"{BASE}/{sensor}/{year}/{name}"
    result = dict(country=country, year=year, sensor=sensor, url=url, path=str(path.resolve()),
                  status="failed", complete=False, coverage_start=f"{year}-01-01T00:00:00Z",
                  coverage_end=f"{year+1}-01-01T00:00:00Z",
                  completeness_basis="Canonical annual CSV validated; satellite observing coverage unknown")
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        if not path.exists():
            if STOP.is_set():
                raise InterruptedError("Download paused by disk reserve guard")
            for attempt in range(3):
                try:
                    request = urllib.request.Request(url, headers={"User-Agent": "FIRETRACE-research/0.1"})
                    with urllib.request.urlopen(request, timeout=90) as source, part.open("wb") as target:
                        expected = int(source.headers.get("Content-Length", "0"))
                        while block := source.read(1024*1024):
                            with LOCK:
                                if STOP.is_set() or shutil.disk_usage(directory).free < reserve + len(block):
                                    STOP.set()
                                    raise InterruptedError("Download paused to preserve 10 GiB free space")
                                target.write(block)
                    if expected and part.stat().st_size != expected:
                        raise ValueError("Transfer length mismatch")
                    _inspect(part)
                    os.replace(part, path)
                    break
                except InterruptedError:
                    part.unlink(missing_ok=True)
                    raise
                except Exception:
                    part.unlink(missing_ok=True)
                    if attempt == 2:
                        raise
                    time.sleep(attempt+1)
        rows, digest = _inspect(path)
        result.update(status="complete", complete=True, rows=rows, sha256=digest, bytes=path.stat().st_size)
    except Exception as error:
        result["error"] = f"{type(error).__name__}: {error}"
    print(f"{country} {sensor} {year}: {result['status']} {result.get('bytes',0):,} bytes", flush=True)
    return result


def download(countries, years, data_dir, workers=3, reserve_gib=10):
    if not 1 <= workers <= 4:
        raise ValueError("Use one to four download workers")
    STOP.clear()
    directory = Path(data_dir)
    directory.mkdir(parents=True, exist_ok=True)
    manifest_path = directory / "manifest.json"
    previous = json.loads(manifest_path.read_text()) if manifest_path.exists() else {"files":[]}
    records = {(r["country"], r["sensor"], r["year"]):r for r in previous["files"]}
    tasks = [(c,y,s) for c in countries for y in years
             for s in ["modis","viirs-snpp"] if s != "viirs-snpp" or y>=2012]
    started = time.monotonic()
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        futures = [pool.submit(fetch,c,y,s,directory,int(reserve_gib*1024**3)) for c,y,s in tasks]
        for future in concurrent.futures.as_completed(futures):
            row = future.result()
            records[(row["country"],row["sensor"],row["year"])] = row
            manifest = {"label":"REAL FIRMS DATA", "source":BASE, "observation_coverage":"unknown",
                        "note":"Complete annual archive availability is not satellite observation coverage.", "files":list(records.values())}
            write_json(manifest_path,manifest)
            good = [r for r in records.values() if r.get("complete")]
            write_json(directory / "progress.json", {"complete_files":len(good), "expected_files":len(tasks),
                      "bytes":sum(r.get("bytes",0) for r in good), "free_bytes":shutil.disk_usage(directory).free,
                      "seconds":round(time.monotonic()-started,1), "stopped_for_reserve":STOP.is_set()})
    if STOP.is_set() or any(not r.get("complete") for r in records.values()):
        raise RuntimeError("One or more annual archives could not be completed; see the saved manifest")

    return manifest
