"""Staged national calibration/evaluation with the unchanged production split rule.

No model is selected from test performance, and nothing is copied to production.
"""
from pathlib import Path
import argparse
import json
import hashlib
import shutil
import time
import numpy as np
import pandas as pd
from .aggregate_archives import peak_rss_bytes, write_json
from pipeline import harmonize
from pipeline.globe import manifest_fingerprint


def seal_locked_artifacts(directory):
    directory = Path(directory)
    names = ["selection_lock.json","harmonization_model.json","harmonization_eval.csv"]
    result = {"note":"Hashes bind saved choices and results; this operation does not run model selection or evaluation.",
              "sha256":{name:hashlib.sha256((directory/name).read_bytes()).hexdigest() for name in names}}
    write_json(directory/"LOCKED_ARTIFACTS.json",result)
    return result


def load_locked_evaluation(analyses, source, output):
    """Verify and reuse saved choices/evaluation without inspecting test results to choose a model."""
    from .prepared_runtime import read_inputs
    manifest,paths,_ = read_inputs(analyses)
    source,output = Path(source),Path(output)
    integrity = json.loads((source/"LOCKED_ARTIFACTS.json").read_text())
    names = ["selection_lock.json","harmonization_model.json","harmonization_eval.csv"]
    for name in names:
        if hashlib.sha256((source/name).read_bytes()).hexdigest()!=integrity["sha256"][name]:
            raise ValueError(f"Locked evaluation artifact changed: {name}")
    model = json.loads((source/"harmonization_model.json").read_text())
    lock = json.loads((source/"selection_lock.json").read_text())
    fingerprint = manifest_fingerprint(manifest)
    if model["archive_manifest_fingerprint"]!=fingerprint or lock["archive_manifest_fingerprint"]!=fingerprint:
        raise ValueError("Locked evaluation and prepared source snapshot differ")
    if model["ratios"]!=lock["ratios"] or model["selection"]!=lock["selection"] or set(model["selection"])!=set(paths):
        raise ValueError("Saved model choices differ from the lock")
    if model["fit_years"]!=harmonize.TRAIN or model["validation_years"]!=harmonize.VALIDATION or model["test_years"]!=harmonize.TEST:
        raise ValueError("Saved evaluation split differs from the predefined split")
    if lock["fit_years"]!=harmonize.TRAIN or lock["validation_years"]!=harmonize.VALIDATION or lock["test_years_reserved"]!=harmonize.TEST:
        raise ValueError("Selection-lock split differs from the predefined split")
    output.mkdir(parents=True,exist_ok=True)
    for name in [*names,"LOCKED_ARTIFACTS.json"]:
        shutil.copyfile(source/name,output/name)
    return model


def evaluate(analyses, output, reference=None):
    output = Path(output)
    output.mkdir(parents=True,exist_ok=True)
    tables, archives, countries, seen = [], [], [], set()
    for directory in analyses:
        directory = Path(directory)
        summary = json.loads((directory/"ANALYSIS_INPUTS.json").read_text())
        manifest = json.loads((directory/"source_manifest.json").read_text())
        for country in summary["countries"]:
            if country in seen:
                raise ValueError(f"Duplicate analysis country: {country}")
            seen.add(country)
            countries.append(country)
            table = pd.read_parquet(directory/f"daily_{country}.parquet")
            tables.append(table[table.cell_id=="ALL"])
        archives.extend(manifest["files"])
    manifest = {"files":archives,"label":"REAL FIRMS DATA","observation_coverage":"unknown"}
    counts = pd.concat(tables,ignore_index=True)
    carrier = pd.DataFrame()
    carrier.attrs["manifest"] = manifest
    availability = {c:{s:harmonize._archive_years(carrier,c,s) for s in ["Terra","Aqua","VIIRS"]} for c in countries}
    common = {c:v["Aqua"]&v["VIIRS"] for c,v in availability.items()}
    fitting = counts[[int(y) in common[c] for c,y in zip(counts.country,counts.year)]]
    started = time.monotonic()
    ratios = harmonize.fit_ratios(fitting)
    selection, whole_tables, rows = {}, {}, []
    for country in sorted(countries):
        viable = availability[country]["Aqua"]|availability[country]["VIIRS"]
        if not viable:
            continue
        dates = pd.date_range(f"{min(viable)}-01-01",f"{max(viable)}-12-31",name="date")
        whole = harmonize._daily(counts,country,"ALL",dates,ratios,availability[country])
        validation = {model:harmonize.metrics(whole.loc[whole.index.year.isin(harmonize.VALIDATION),"Aqua"],
                     whole.loc[whole.index.year.isin(harmonize.VALIDATION),model])["mae"] for model in ["B1","M1"]}
        selected = "M1" if validation["M1"] is not None and validation["B1"] is not None and validation["M1"]<validation["B1"] else "B1"
        selection[country] = {"selected":selected,"validation_daily_mae":validation}
        whole_tables[country] = whole
    # Persist every country's final choice before any held-out evaluation.
    lock = {"fit_years":harmonize.TRAIN,"validation_years":harmonize.VALIDATION,
            "test_years_reserved":harmonize.TEST,"ratios":ratios,"selection":selection,
            "archive_manifest_fingerprint":manifest_fingerprint(manifest),
            "policy":"Selection locked from training and validation only, before test evaluation."}
    lock_path = output/"selection_lock.json"
    if lock_path.exists() and json.loads(lock_path.read_text()) != lock:
        raise ValueError("A different selection is already locked in this directory; preserve it and use a new output")
    write_json(lock_path,lock)
    for country, whole in whole_tables.items():
        for model in ["B0","B1","M1"]:
            rows.extend(harmonize._evaluate(whole,country,model,"validation",harmonize.VALIDATION))
            rows.extend(harmonize._evaluate(whole,country,model,"test",harmonize.TEST))
    evaluation = pd.DataFrame(rows)
    evaluation["label"] = "REAL FIRMS DATA"
    evaluation.to_csv(output/"harmonization_eval.csv",index=False)
    result = {"phase":"prepared-count evaluation","fit_years":harmonize.TRAIN,
              "validation_years":harmonize.VALIDATION,"test_years":harmonize.TEST,"ratios":ratios,"selection":selection,
              "archive_files":len(archives),"archive_manifest_fingerprint":manifest_fingerprint(manifest),
              "seconds":round(time.monotonic()-started,2),"peak_rss_bytes":peak_rss_bytes(),
              "policy":"Country selection uses validation daily MAE only; the test split is reported without changing the selection rule."}
    if reference:
        original = pd.read_csv(reference)
        keys = ["region","model","split","aggregation"]
        a, b = original.sort_values(keys).reset_index(drop=True), evaluation.sort_values(keys).reset_index(drop=True)
        if len(a)!=len(b) or not a[keys].equals(b[keys]):
            raise ValueError("Reference comparison requires the same countries and evaluation rows")
        numeric = [c for c in a.select_dtypes(include="number").columns if c in b]
        np.testing.assert_allclose(a[numeric],b[numeric],rtol=1e-12,atol=1e-10,equal_nan=True)
        result["reference_comparison"] = {"status":"pass","rows":len(a),"numeric_fields":numeric,
                                          "maximum_absolute_difference":float(np.nanmax(np.abs(a[numeric].to_numpy()-b[numeric].to_numpy())))}
    write_json(output/"harmonization_model.json",result)
    seal_locked_artifacts(output)
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("analyses",nargs="+")
    parser.add_argument("--output",required=True)
    parser.add_argument("--reference")
    args = parser.parse_args()
    result = evaluate(args.analyses,args.output,args.reference)
    print(json.dumps({k:v for k,v in result.items() if k!="ratios"},indent=2))
