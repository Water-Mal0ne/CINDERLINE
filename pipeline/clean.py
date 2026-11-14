"""FIRMS cleaning with explicit civil time, stream provenance and unknown coverage."""
from __future__ import annotations
import json
from pathlib import Path
import numpy as np
import pandas as pd

FIXED_ZONES = {"Nepal": "Asia/Kathmandu", "India": "Asia/Kolkata", "Bangladesh": "Asia/Dhaka", "Egypt": "Africa/Cairo"}
_TIMEZONE_FINDER = None


def _utc_datetime(frame):
    numeric = pd.to_numeric(frame["acq_time"], errors="coerce")
    valid = numeric.notna() & (numeric == np.floor(numeric)) & numeric.between(0, 2359) & ((numeric % 100) < 60)
    text = numeric.where(valid).astype("Int64").astype(str).str.zfill(4)
    return pd.to_datetime(frame["acq_date"].astype(str) + " " + text, format="%Y-%m-%d %H%M", errors="coerce", utc=True)


def clean_frame(frame, country=None, grid_size=0.25):
    """Clean one or several archives; unknown fire type remains -1, never vegetation."""
    df = frame.copy()
    if country is not None:
        df["country"] = country
    diagnostics = {"rows_input": int(len(df)), "invalid_timestamps": 0, "unresolved_zones": 0}
    inst = df.get("instrument", pd.Series("", index=df.index)).astype(str).str.upper()
    sat = df["satellite"].astype(str).str.upper()
    df["stream"] = np.select([inst.str.contains("VIIRS") | sat.isin(["N", "SUOMI-NPP", "S-NPP"]),
                              sat.isin(["T", "TERRA"]), sat.isin(["A", "AQUA"])],
                             ["VIIRS", "Terra", "Aqua"], default="unknown")
    conf = df["confidence"].astype(str).str.lower().str.strip()
    keep = ((df.stream == "VIIRS") & conf.isin(["n", "h", "nominal", "high"])) | \
           (df.stream.isin(["Terra", "Aqua"]) & (pd.to_numeric(conf, errors="coerce") >= 30))
    diagnostics["confidence_or_stream_excluded"] = int((~keep).sum())
    df = df[keep].copy()
    # MODIS uses numeric confidence, VIIRS categorical confidence: preserve both as text.
    df["confidence"] = df["confidence"].astype(str)
    df["utc"] = _utc_datetime(df)
    diagnostics["invalid_timestamps"] = int(df.utc.isna().sum())
    df["lat"] = pd.to_numeric(df["latitude"], errors="coerce")
    df["lon"] = pd.to_numeric(df["longitude"], errors="coerce")
    coords_ok = df.lat.between(-90, 90) & df.lon.between(-180, 180)
    diagnostics["invalid_coordinates"] = int((~coords_ok).sum())
    df = df[df.utc.notna() & coords_ok].copy()
    df["type"] = pd.to_numeric(df.get("type", pd.Series(-1, index=df.index)), errors="coerce").fillna(-1).astype(int)
    df["frp"] = pd.to_numeric(df.get("frp", pd.Series(np.nan, index=df.index)), errors="coerce")
    df["daynight"] = df.get("daynight", pd.Series("?", index=df.index)).fillna("?").astype(str).str.upper()
    df["grid_lat"] = np.floor(df.lat / grid_size) * grid_size
    df["grid_lon"] = np.floor(df.lon / grid_size) * grid_size
    df["cell_id"] = df.grid_lat.map(lambda x: f"{x:.2f}").astype(str) + ":" + df.grid_lon.map(lambda x: f"{x:.2f}").astype(str)
    local = pd.Series(pd.NaT, index=df.index, dtype="datetime64[ns]")
    zone_names = pd.Series(None, index=df.index, dtype=object)
    global _TIMEZONE_FINDER
    tf = _TIMEZONE_FINDER
    for country_name, group in df.groupby("country"):
        zone = FIXED_ZONES.get(country_name)
        if zone:
            zone_names.loc[group.index] = zone
            continue
        if tf is None:
            from timezonefinder import TimezoneFinder
            tf = TimezoneFinder(in_memory=True)
            _TIMEZONE_FINDER = tf
        # Exact coordinates: do not let a rounded spatial grid cross civil-time boundaries.
        zone_names.loc[group.index] = [tf.timezone_at(lat=a, lng=b) for a, b in zip(group.lat, group.lon)]
    for zone, indexes in zone_names.dropna().groupby(zone_names.dropna()).groups.items():
        local.loc[indexes] = df.loc[indexes, "utc"].dt.tz_convert(zone).dt.tz_localize(None)
    diagnostics["unresolved_zones"] = int(local.isna().sum())
    df["local"] = local
    df["timezone"] = zone_names
    df = df[df.local.notna()].copy()
    df["local_date"] = df.local.dt.normalize()
    df["weekday"] = df.local.dt.dayofweek
    df["year"] = df.local.dt.year
    diagnostics["date_changed"] = int((df.local.dt.date != df.utc.dt.date).sum())
    diagnostics["unknown_type"] = int((df.type == -1).sum())
    diagnostics["rows_output"] = int(len(df))
    columns = ["country", "stream", "utc", "local", "local_date", "weekday", "year", "lat", "lon", "cell_id", "frp", "daynight", "type", "confidence", "timezone"]
    for optional in ["file_year", "source_file", "label"]:
        if optional in df:
            columns.append(optional)
    out = df[columns].reset_index(drop=True)
    out.attrs["diagnostics"] = diagnostics
    return out


def load_clean(data_dir, countries=None):
    """Load archives, retaining type1/2 for controls. Write cleaning diagnostics beside manifest."""
    directory = Path(data_dir)
    manifest_path = directory / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else {"label": "UNVERIFIED INPUT", "files": []}
    frames, summaries = [], []
    cache_dir = directory.parent / "processed" / "clean_cache_v2"
    cache_dir.mkdir(parents=True, exist_ok=True)
    for path in sorted(directory.rglob("*.csv")):
        parts = path.stem.split("_", 2)
        if len(parts) != 3 or not parts[1].isdigit():
            continue
        if countries is not None and parts[2] not in countries:
            continue
        cached = cache_dir / (path.stem + ".parquet")
        if cached.exists() and cached.stat().st_mtime >= path.stat().st_mtime:
            result = pd.read_parquet(cached)
        else:
            frame = pd.read_csv(path, low_memory=False)
            frame["file_year"] = int(parts[1])
            frame["source_file"] = str(path)
            result = clean_frame(frame, parts[2])
            result.to_parquet(cached, index=False)
        summaries.append({"file": str(path), **result.attrs["diagnostics"]})
        frames.append(result)
        print(f"Cleaned {path.name}: {len(result):,} records", flush=True)
    if not frames:
        raise FileNotFoundError(f"No FIRMS archives under {directory}")
    out = pd.concat(frames, ignore_index=True)
    for column in ["country", "stream", "daynight", "timezone", "cell_id", "source_file"]:
        out[column] = out[column].astype("category")
    label = manifest.get("label", "UNVERIFIED INPUT")
    out["label"] = label
    out.attrs.update(manifest=manifest, label=label, diagnostics=summaries)
    (directory / "cleaning_diagnostics.json").write_text(json.dumps(summaries, indent=2), encoding="utf-8")
    return out
