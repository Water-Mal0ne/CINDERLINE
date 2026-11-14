"""Staged per-country conversion from exact counts and a locked fitted model."""
from pathlib import Path
import argparse
import json
import time
import numpy as np
import pandas as pd
from .aggregate_archives import write_json, peak_rss_bytes
from pipeline import harmonize
from pipeline.globe import manifest_fingerprint


def read_inputs(analyses):
    archives, paths, selected = [], {}, {}
    for directory in map(Path,analyses):
        summary = json.loads((directory/"ANALYSIS_INPUTS.json").read_text())
        archives.extend(json.loads((directory/"source_manifest.json").read_text())["files"])
        for country in summary["countries"]:
            if country in paths:
                raise ValueError(f"Duplicate country: {country}")
            paths[country] = directory/f"daily_{country}.parquet"
            selected[country] = summary["selected_cells"][country]
    return {"label":"REAL FIRMS DATA","files":archives,"observation_coverage":"unknown"},paths,selected


def run_preaggregated(analyses, model_path, output):
    output = Path(output)
    output.mkdir(parents=True,exist_ok=True)
    started = time.monotonic()
    manifest, paths, cells = read_inputs(analyses)
    model = json.loads(Path(model_path).read_text())
    fingerprint = manifest_fingerprint(manifest)
    if model["archive_manifest_fingerprint"] != fingerprint:
        raise ValueError("Locked model and prepared archives differ")
    carrier = pd.DataFrame()
    carrier.attrs["manifest"] = manifest
    availability = {c:{s:harmonize._archive_years(carrier,c,s) for s in ["Terra","Aqua","VIIRS"]} for c in paths}
    tables = []
    for country,path in paths.items():
        counts = pd.read_parquet(path)
        common = availability[country]["Aqua"]&availability[country]["VIIRS"]
        tables.append(counts[(counts.cell_id=="ALL")&counts.year.isin(common)])
    fitting = pd.concat(tables,ignore_index=True)
    if harmonize.fit_ratios(fitting) != model["ratios"]:
        raise ValueError("Locked ratios do not match unchanged training fit")
    rng = np.random.default_rng(2841)
    years = sorted(set(fitting[fitting.year.isin(harmonize.TRAIN)].year))
    bootstrap = []
    for _ in range(harmonize.N_BOOT):
        sampled = rng.choice(years,size=len(years),replace=True)
        resampled = pd.concat([fitting[fitting.year==y] for y in sampled],ignore_index=True)
        bootstrap.append(harmonize.fit_ratios(resampled))
    written = []
    for country in sorted(paths):
        counts = pd.read_parquet(paths[country])
        viable = availability[country]["Aqua"]|availability[country]["VIIRS"]
        if not viable:
            continue
        dates = pd.date_range(f"{min(viable)}-01-01",f"{max(viable)}-12-31",name="date")
        date_strings = dates.strftime("%Y-%m-%d")
        selected_model = model["selection"][country]["selected"]
        coverage_by_year = {year:"archive: "+",".join(s for s in ["Terra","Aqua","VIIRS"] if year in availability[country][s])+"; observation coverage unknown" for year in dates.year.unique()}
        frames = []
        for cell in ["ALL",*cells[country]]:
            daily = harmonize._daily(counts,country,cell,dates,model["ratios"],availability[country])
            viirs = counts[(counts.cell_id==cell)&(counts.stream=="VIIRS")]
            draws = harmonize.bootstrap_daily(viirs,dates,country,selected_model,bootstrap)
            lo,hi = np.percentile(draws,[2.5,97.5],axis=0)
            prediction = daily[selected_model].to_numpy()
            converted = np.isfinite(prediction)
            source = np.where(converted,"converted VIIRS",np.where(daily.Aqua.notna(),"observed Aqua","unavailable"))
            frames.append(pd.DataFrame({"date":date_strings,"region":country,"cell_id":cell,
                "raw_terra":daily.Terra.to_numpy(),"raw_aqua":daily.Aqua.to_numpy(),"raw_viirs":daily.VIIRS.to_numpy(),
                "raw":harmonize.raw_display_series(daily).to_numpy(),"harmonized":np.where(converted,prediction,daily.Aqua),
                "lo":np.where(converted,lo,daily.Aqua),"hi":np.where(converted,hi,daily.Aqua),
                "coverage":[coverage_by_year[y] for y in dates.year],"source":source,
                "model":np.where(converted,selected_model,"Aqua reference"),"label":"REAL FIRMS DATA"}))
        result = pd.concat(frames,ignore_index=True)
        result.attrs.update(label="REAL FIRMS DATA",manifest=manifest,model_selection=model["selection"],model_revision=model.get("model_revision"))
        filename = f"harmonized_{country}.parquet"
        result.to_parquet(output/filename,index=False)
        written.append({"country":country,"file":filename,"rows":len(result)})
        print(f"Converted {country}: {len(result):,} daily rows",flush=True)
    report = {"phase":"prepared-count pipeline","archive_manifest_fingerprint":fingerprint,"archive_files":len(manifest["files"]),
              "bootstrap_draws":harmonize.N_BOOT,"files":written,"seconds":round(time.monotonic()-started,2),
              "peak_rss_bytes":peak_rss_bytes(),"source_model":str(model_path),"model_revision":model.get("model_revision")}
    write_json(output/"CONVERSION.json",report)
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("analyses",nargs="+")
    parser.add_argument("--model",required=True)
    parser.add_argument("--output",required=True)
    args = parser.parse_args()
    print(json.dumps(run_preaggregated(args.analyses,args.model,args.output),indent=2))
