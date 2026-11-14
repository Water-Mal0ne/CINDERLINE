"""Isolated phase-3 streaming preparation. Does not alter production code or exports.

Cell-stat partitions may contain the same cell/day key across chunks. Consumers
must sum `n` (and FRP sums/counts), never count summary rows as detections.
"""
from __future__ import annotations
import argparse
from collections import defaultdict
import ctypes
import hashlib
import json
import os
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
import numpy as np
import pandas as pd
from pipeline.clean import clean_frame
from pipeline.harmonize import _strata

CELL_KEYS = ["country", "stream", "local_date", "year", "weekday", "cell_id", "daynight", "type", "stratum"]
FIT_KEYS = ["country", "stream", "year", "daynight", "type", "stratum"]
RHYTHM_KEYS = ["country", "stream", "year", "weekday", "daynight", "type"]


def peak_rss_bytes():
    if os.name != "nt":
        try:
            import resource
            return int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * (1 if sys.platform == "darwin" else 1024))
        except ImportError:
            return None
    class Counters(ctypes.Structure):
        _fields_ = [("cb", ctypes.c_ulong), ("PageFaultCount", ctypes.c_ulong),
                    *[(name, ctypes.c_size_t) for name in ["PeakWorkingSetSize", "WorkingSetSize", "QuotaPeakPagedPoolUsage", "QuotaPagedPoolUsage", "QuotaPeakNonPagedPoolUsage", "QuotaNonPagedPoolUsage", "PagefileUsage", "PeakPagefileUsage"]]]
    counters = Counters()
    counters.cb = ctypes.sizeof(counters)
    current_process = ctypes.windll.kernel32.GetCurrentProcess
    current_process.restype = ctypes.c_void_p
    memory_info = ctypes.windll.psapi.GetProcessMemoryInfo
    memory_info.argtypes = [ctypes.c_void_p, ctypes.POINTER(Counters), ctypes.c_ulong]
    memory_info.restype = ctypes.c_int
    ok = memory_info(current_process(), ctypes.byref(counters), counters.cb)
    return int(counters.PeakWorkingSetSize) if ok else None


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def write_json(path, payload):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, indent=2, allow_nan=False), encoding="utf-8")
    os.replace(temporary, path)


def sufficient_stats(cleaned):
    """Exact integer counts after existing quality/local-time cleaning rules."""
    frame = cleaned.copy()
    frame["stratum"] = _strata(frame)
    frame["frp_value"] = pd.to_numeric(frame.frp, errors="coerce").fillna(0.)
    frame["frp_known"] = pd.to_numeric(frame.frp, errors="coerce").notna().astype("int64")
    cells = frame.groupby(CELL_KEYS, observed=True, dropna=False).agg(
        n=("stream", "size"), frp_sum=("frp_value", "sum"), frp_known=("frp_known", "sum")).reset_index()
    fits = frame.groupby(FIT_KEYS, observed=True, dropna=False).size().rename("n").reset_index()
    rhythms = frame.groupby(RHYTHM_KEYS, observed=True, dropna=False).size().rename("n").reset_index()
    return cells, fits, rhythms


def add_totals(target, frame, keys):
    for row in frame[keys + ["n"]].itertuples(index=False, name=None):
        key = tuple(value.item() if isinstance(value, np.generic) else value for value in row[:-1])
        target[key] += int(row[-1])


def totals_frame(values, keys):
    return pd.DataFrame([(*key, int(n)) for key, n in sorted(values.items())], columns=[*keys, "n"])


def process_archive(record, output, chunk_size=200_000, write_clean=False):
    source = Path(record["path"])
    expected_hash = record.get("sha256")
    if not record.get("complete") or record.get("status") != "complete" or not expected_hash:
        raise ValueError("Only verified complete archive records with hashes may be processed")
    actual_hash = sha256(source)
    if actual_hash != expected_hash:
        raise ValueError(f"Archive bytes differ from manifest: {source}")
    source_dir = Path(output) / "archives" / record["country"] / record["sensor"] / str(record["year"])
    source_dir.mkdir(parents=True, exist_ok=True)
    code_hash = hashlib.sha256((sha256(__file__) + sha256(ROOT / "pipeline/clean.py") + sha256(ROOT / "pipeline/harmonize.py")).encode()).hexdigest()
    signature = dict(source_sha256=actual_hash, code_sha256=code_hash, chunk_size=chunk_size, write_clean=write_clean)
    complete = source_dir / "done.json"
    if complete.exists():
        saved = json.loads(complete.read_text(encoding="utf-8"))
        if saved.get("signature") == signature and all((Path(output) / name).exists() for name in saved["outputs"]):
            saved["reused"] = True
            return saved
    started = time.monotonic()
    fit_total, rhythm_total = defaultdict(int), defaultdict(int)
    diagnostics = defaultdict(int)
    raw_rows = cleaned_rows = count_rows = 0
    output_files = []
    chunk_count = 0
    for i, raw in enumerate(pd.read_csv(source, chunksize=chunk_size, low_memory=False)):
        raw_rows += len(raw)
        raw["file_year"] = int(record["year"])
        raw["source_file"] = str(source)
        cleaned = clean_frame(raw, country=record["country"])
        for name, value in cleaned.attrs["diagnostics"].items():
            diagnostics[name] += int(value)
        cleaned_rows += len(cleaned)
        cells, fit, rhythm = sufficient_stats(cleaned)
        count_rows += len(cells)
        metadata = {"label": "REAL FIRMS DATA", "source_url": record["url"], "source_sha256": actual_hash,
                    "archive_year": record["year"], "source_chunk": i,
                    "observation_coverage": "unknown", "representation": "Exact aggregated detection counts; n is the row multiplicity"}
        cells.attrs = metadata
        stats_path = source_dir / f"counts-{i:05}.parquet"
        cells.to_parquet(stats_path, index=False)
        output_files.append(str(stats_path.relative_to(output)))
        if write_clean:
            cleaned.attrs.update(label="REAL FIRMS DATA", source_url=record["url"], source_sha256=actual_hash)
            clean_path = source_dir / f"detections-{i:05}.parquet"
            cleaned.to_parquet(clean_path, index=False)
            output_files.append(str(clean_path.relative_to(output)))
        add_totals(fit_total, fit, FIT_KEYS)
        add_totals(rhythm_total, rhythm, RHYTHM_KEYS)
        chunk_count += 1
    if raw_rows != int(record["rows"]):
        raise ValueError(f"Row count mismatch: {source}, manifest={record['rows']}, read={raw_rows}")
    for filename, table in [("fit.parquet", totals_frame(fit_total, FIT_KEYS)), ("rhythm.parquet", totals_frame(rhythm_total, RHYTHM_KEYS))]:
        table.attrs = {"label": "REAL FIRMS DATA", "source_sha256": actual_hash, "representation": "Exact integer counts"}
        path = source_dir / filename
        table.to_parquet(path, index=False)
        output_files.append(str(path.relative_to(output)))
    result = {"country": record["country"], "sensor": record["sensor"], "year": record["year"], "signature": signature,
              "raw_rows": raw_rows, "cleaned_rows": cleaned_rows, "cell_stat_rows": count_rows, "chunks": chunk_count,
              "outputs": output_files, "diagnostics": dict(diagnostics), "seconds": round(time.monotonic() - started, 3),
              "peak_rss_bytes": peak_rss_bytes(), "reused": False}
    write_json(complete, result)
    return result


def prepare(manifest_path, countries, output, chunk_size=200_000, write_clean=False):
    started = time.monotonic()
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    manifest = json.loads(Path(manifest_path).read_text(encoding="utf-8"))
    files = [r for r in manifest["files"] if r["country"] in countries]
    files.sort(key=lambda r: (r["country"], r["year"], r["sensor"]))
    if not files:
        raise ValueError("No selected countries in input manifest")
    write_json(output / "source_manifest.json", {**manifest, "files": files})
    done, fits, rhythms = [], defaultdict(int), defaultdict(int)
    for record in files:
        result = process_archive(record, output, chunk_size, write_clean)
        done.append(result)
        archive = output / "archives" / record["country"] / record["sensor"] / str(record["year"])
        add_totals(fits, pd.read_parquet(archive / "fit.parquet"), FIT_KEYS)
        add_totals(rhythms, pd.read_parquet(archive / "rhythm.parquet"), RHYTHM_KEYS)
        write_json(output / "progress.json", {"archives_done": len(done), "archives_total": len(files),
                                               "raw_rows": sum(r["raw_rows"] for r in done), "cleaned_rows": sum(r["cleaned_rows"] for r in done),
                                               "peak_rss_bytes": peak_rss_bytes()})
        print(f"{len(done)}/{len(files)} {record['country']} {record['sensor']} {record['year']}: {result['cleaned_rows']:,} cleaned / {result['cell_stat_rows']:,} count rows", flush=True)
    totals_frame(fits, FIT_KEYS).to_parquet(output / "fit_counts.parquet", index=False)
    totals_frame(rhythms, RHYTHM_KEYS).to_parquet(output / "rhythm_counts.parquet", index=False)
    report = {"phase": "prepared-count preparation", "label": "REAL FIRMS DATA", "countries": countries,
              "archive_count": len(done), "raw_rows": sum(r["raw_rows"] for r in done),
              "cleaned_rows": sum(r["cleaned_rows"] for r in done), "cell_stat_rows": sum(r["cell_stat_rows"] for r in done),
              "chunks": sum(r["chunks"] for r in done), "chunk_size": chunk_size,
              "seconds": round(time.monotonic() - started, 2), "peak_rss_bytes": peak_rss_bytes(),
              "output_bytes": sum(p.stat().st_size for p in output.rglob("*.parquet")),
              "clean_partitions_written": write_clean, "archives": done,
              "contract": {"cell_counts": CELL_KEYS + ["n", "frp_sum", "frp_known"], "fit_counts": FIT_KEYS + ["n"], "rhythm_counts": RHYTHM_KEYS + ["n"]},
              "limitations": ["Summary rows are not individual detections; always sum n.", "File-year partitions can share a local-date key at UTC boundaries; sum across partitions.",
                              "FRP sums with frp_known=0 are unknown, not measured zero.", "All original archives and their hashes are retained.",
                              "No model is refitted and no release gate evaluated by this preparation step."]}
    write_json(output / "PREPARATION.json", report)
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", default=str(ROOT / "data/raw/manifest.json"))
    parser.add_argument("--countries", nargs="+", default=["Bangladesh", "Egypt"])
    parser.add_argument("--output", default=str(ROOT / "work/phase3/bangladesh-egypt"))
    parser.add_argument("--chunk-size", type=int, default=200_000)
    parser.add_argument("--write-clean", action="store_true")
    args = parser.parse_args()
    result = prepare(args.manifest, args.countries, args.output, args.chunk_size, args.write_clean)
    print(json.dumps({k: v for k, v in result.items() if k not in ["archives", "contract"]}, indent=2), flush=True)
