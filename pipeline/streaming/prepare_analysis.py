"""Disk-backed reduction of verified count partitions; no model fitting or release.

The database stores exact additive counts. Its national and selected-cell daily
outputs match harmonize.run's input, while annual output retains every grid cell.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import sqlite3
import time

import pandas as pd
from .aggregate_archives import peak_rss_bytes, write_json
from pipeline.harmonize import TRAIN, MAX_CELLS, _archive_years
from pipeline.globe import manifest_fingerprint

DAILY_KEYS = ["country", "cell_id", "date", "year", "stratum", "stream"]
ANNUAL_KEYS = ["country", "cell_id", "year", "stratum", "stream"]


def upsert(connection, table, frame, keys):
    columns = keys+["n"]
    statement = f"INSERT INTO {table} ({','.join(columns)}) VALUES ({','.join('?' for _ in columns)}) "
    statement += f"ON CONFLICT ({','.join(keys)}) DO UPDATE SET n={table}.n+excluded.n"
    connection.executemany(statement, frame[columns].itertuples(index=False, name=None))


def create_table(connection, table, keys):
    declarations = [f"{key} {'INTEGER' if key=='year' else 'TEXT'} NOT NULL" for key in keys]
    connection.execute(f"CREATE TABLE {table} ({','.join(declarations)}, n INTEGER NOT NULL, PRIMARY KEY ({','.join(keys)})) WITHOUT ROWID")


def input_snapshot(preparations):
    files, paths, seen = [], [], set()
    for directory in preparations:
        directory = Path(directory)
        report = json.loads((directory / "PREPARATION.json").read_text(encoding="utf-8"))
        manifest = json.loads((directory / "source_manifest.json").read_text(encoding="utf-8"))
        if len(report["archives"]) != len(manifest["files"]):
            raise ValueError(f"Incomplete preparation: {directory}")
        by_key = {(r["country"],r["sensor"],r["year"]):r for r in manifest["files"]}
        for archive in report["archives"]:
            key = (archive["country"],archive["sensor"],archive["year"])
            if key in seen:
                raise ValueError(f"Duplicate archive in input preparations: {key}")
            seen.add(key)
            source = by_key[key]
            if not source.get("complete") or source.get("sha256") != archive["signature"]["source_sha256"]:
                raise ValueError(f"Unverified source preparation: {key}")
            files.append(source)
            for name in archive["outputs"]:
                if Path(name).name.startswith("counts-"):
                    path = directory / name
                    if not path.exists():
                        raise ValueError(f"Missing count partition: {path}")
                    paths.append(path)
    return {"files":files,"label":"REAL FIRMS DATA","observation_coverage":"unknown"}, paths


def build(preparations, output):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    database = output / "analysis.sqlite"
    if database.exists():
        raise ValueError("Use a fresh output directory; existing staged databases are preserved")
    manifest, partitions = input_snapshot(preparations)
    countries = sorted({r["country"] for r in manifest["files"]})
    started = time.monotonic()
    connection = sqlite3.connect(database)
    connection.execute("PRAGMA cache_size=-65536")  # 64 MiB page cache
    connection.execute("PRAGMA temp_store=FILE")
    create_table(connection,"daily",DAILY_KEYS)
    create_table(connection,"annual",ANNUAL_KEYS)
    create_table(connection,"training",["country","cell_id"])
    vegetation_rows = 0
    for i,path in enumerate(partitions):
        frame = pd.read_parquet(path)
        frame = frame[frame.type==0].copy()
        vegetation_rows += int(frame.n.sum())
        frame["date"] = pd.to_datetime(frame.local_date).dt.strftime("%Y-%m-%d")
        annual = frame.groupby(ANNUAL_KEYS,observed=True).n.sum().reset_index()
        upsert(connection,"annual",annual,ANNUAL_KEYS)
        national = frame.groupby([k for k in DAILY_KEYS if k!="cell_id"],observed=True).n.sum().reset_index()
        national["cell_id"] = "ALL"
        upsert(connection,"daily",national,DAILY_KEYS)
        training = frame[frame.year.isin(TRAIN)].groupby(["country","cell_id"],observed=True).n.sum().reset_index()
        upsert(connection,"training",training,["country","cell_id"])
        connection.commit()
        if (i+1)%20==0 or i+1==len(partitions):
            print(f"First pass {i+1}/{len(partitions)} partitions",flush=True)
    selected = {}
    for country in countries:
        rows = connection.execute("SELECT cell_id FROM training WHERE country=? ORDER BY n DESC,cell_id ASC LIMIT ?",(country,MAX_CELLS))
        selected[country] = [row[0] for row in rows]
    for i,path in enumerate(partitions):
        frame = pd.read_parquet(path)
        if frame.empty:
            continue
        countries_in_partition = frame.country.unique()
        wanted = set().union(*(set(selected[c]) for c in countries_in_partition))
        frame = frame[(frame.type==0)&frame.cell_id.isin(wanted)].copy()
        frame = frame[[cell in selected[c] for c,cell in zip(frame.country,frame.cell_id)]]
        if frame.empty:
            continue
        frame["date"] = pd.to_datetime(frame.local_date).dt.strftime("%Y-%m-%d")
        daily = frame.groupby(DAILY_KEYS,observed=True).n.sum().reset_index()
        upsert(connection,"daily",daily,DAILY_KEYS)
        connection.commit()
    daily_paths, annual_paths = [], []
    for country in countries:
        frame = pd.read_sql_query("SELECT * FROM daily WHERE country=? ORDER BY country,cell_id,date,year,stratum,stream",connection,params=(country,))
        frame["date"] = pd.to_datetime(frame.date)
        frame.attrs = {"manifest":manifest,"label":"REAL FIRMS DATA","representation":"Exact detection counts; sum n"}
        path = output / f"daily_{country}.parquet"
        frame.to_parquet(path,index=False)
        daily_paths.append(path.name)
        years = [row[0] for row in connection.execute("SELECT DISTINCT year FROM annual WHERE country=? ORDER BY year",(country,))]
        for year in years:
            annual = pd.read_sql_query("SELECT * FROM annual WHERE country=? AND year=? ORDER BY cell_id,stratum,stream",connection,params=(country,year))
            annual.attrs = frame.attrs
            path = output / f"annual_{country}_{year}.parquet"
            annual.to_parquet(path,index=False)
            annual_paths.append(path.name)
    sizes = {table:int(connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]) for table in ["daily","annual","training"]}
    connection.close()
    carrier = pd.DataFrame()
    carrier.attrs["manifest"] = manifest
    availability = {c:{s:sorted(_archive_years(carrier,c,s)) for s in ["Terra","Aqua","VIIRS"]} for c in countries}
    report = {"phase":"prepared-count reduction", "countries":countries,
              "archive_files":len(manifest["files"]), "archive_manifest_fingerprint":manifest_fingerprint(manifest),
              "source_partitions":len(partitions),"vegetation_detections":vegetation_rows,
              "selected_cells":selected,"availability":availability,"rows":sizes,
              "daily_files":daily_paths,"annual_files":annual_paths,
              "seconds":round(time.monotonic()-started,2),"peak_rss_bytes":peak_rss_bytes(),
              "output_bytes":sum(p.stat().st_size for p in output.iterdir() if p.is_file()),
              "limitations":["Annual outputs retain separate streams and must apply eligibility/source choice before summing.",
                             "Daily national totals include all vegetation cells; detailed daily cells use training activity only.",
                             "Archive completeness does not measure satellite/cloud observation exposure.",
                             "Only verified input preparations are accepted; no partially downloaded country is published."]}
    write_json(output / "source_manifest.json",manifest)
    write_json(output / "ANALYSIS_INPUTS.json",report)
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("preparations",nargs="+")
    parser.add_argument("--output",required=True)
    args = parser.parse_args()
    report = build(args.preparations,args.output)
    print(json.dumps({k:v for k,v in report.items() if k not in ["daily_files","annual_files","availability","selected_cells"]},indent=2))
