"""Staged exact-count adapter for rhythm inference; production code stays frozen.

Counts originate from aggregate_archives after civil-date conversion. The inference
algorithm and RNG keys match pipeline.rhythm; only multiplicity and the explicit
instrument commissioning-year qualification differ.
"""
from pathlib import Path
import sys
import json
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from pipeline import rhythm
from pipeline.harmonize import FIRST_COMPLETE_YEAR


def validate_counts(frame):
    required = {"country", "stream", "year", "weekday", "daynight", "type", "n"}
    if not required.issubset(frame):
        raise ValueError(f"Missing sufficient-count columns: {sorted(required-set(frame))}")
    for name in ["year", "weekday", "type", "n"]:
        values = pd.to_numeric(frame[name], errors="coerce")
        if values.isna().any() or (~np.isfinite(values)).any() or (values % 1 != 0).any():
            raise ValueError(f"{name} must contain finite integers")
    if (frame.n < 0).any() or not frame.weekday.between(0,6).all():
        raise ValueError("Counts must be nonnegative and weekdays must be 0–6")
    if not frame.country.isin(rhythm.REST_DAYS).all() or not frame.stream.isin(rhythm.STREAMS).all():
        raise ValueError("Unrecognized country or satellite stream")
    return frame


def verified_local_year(manifest, country, stream, year):
    # Annual MODIS files include Terra before Aqua begins; file presence alone
    # cannot establish a complete Aqua year. Explicit attestations cannot either.
    return year >= FIRST_COMPLETE_YEAR[stream] and rhythm.verified_local_year(manifest,country,stream,year)


def analyse_stream(sub, country, stream, subset, manifest, config, control=False):
    years, exploratory, excluded = [], [], []
    verified, exploratory_years = [], []
    used_detections = 0
    for raw_year, group in sub.groupby("year", sort=True):
        year = int(raw_year)
        detections = int(group.n.sum())
        if year >= config["as_of_year"] or detections < config["min_detections_per_year"]:
            excluded.append({"year":year,"detections":detections,"reason":"incomplete current/future year or low count"})
            continue
        counts = np.bincount(group.weekday.astype(int), weights=group.n.to_numpy(float), minlength=7).astype(float)
        rate = counts / rhythm.weekday_exposure(year)
        index = rate / rate.mean()
        if verified_local_year(manifest,country,stream,year):
            years.append(index)
            verified.append(year)
            used_detections += detections
        else:
            exploratory.append(index)
            exploratory_years.append(year)
    result = {"country":country,"stream":stream,"subset":subset,
              "rest_day":rhythm.REST_DAYS[country],"status":"insufficient_data",
              "years":len(verified),"year_list":verified,"detections":int(sub.n.sum()),
              "detections_used":int(used_detections),"period_verified":True,
              "unverified_years":exploratory_years,"excluded_years":excluded,
              "weekdays":[],"p_null":None,"p_adjusted":None,
              "rest_is_lowest":False,"ci_upper_below_one":False,"significant":False}
    if len(years) < config["min_years"]:
        if len(years)+len(exploratory) < config["min_years"]:
            result["reason"] = "Fewer than the required years of detections."
            return result
        years = years+exploratory
        result.update(period_verified=False, years=len(years), year_list=sorted(verified+exploratory_years),
                      reason="Exploratory estimate: input-period completeness is unverified.")
    else:
        result["status"] = "ok"
        result["reason"] = "Annual archive coverage verified; actual observing exposure remains unknown."
    Y = np.asarray(years)
    n = len(Y)
    rng = rhythm._rng(config["seed"], f"{country}|{stream}|{subset}|{control}|{result['year_list']}")
    boots = Y[rng.integers(0,n,(config["bootstrap_draws"],n))].mean(axis=1)
    random_days = rng.integers(0,7,(config["null_draws"],n))
    null = Y[np.arange(n)[None,:],random_days].mean(axis=1)
    mean = Y.mean(axis=0)
    lo, hi = np.percentile(boots,[2.5,97.5],axis=0)
    r = rhythm.DAYS.index(rhythm.REST_DAYS[country])
    p = float((np.count_nonzero(null<=mean[r])+1)/(len(null)+1))
    m = len(rhythm.REST_DAYS)*len(rhythm.STREAMS)
    p_adj = min(p*m,1.0)
    lowest = bool(mean[r] == mean.min())
    result.update(weekdays=[{"day":d,"index":float(mean[i]),"lo":float(lo[i]),"hi":float(hi[i])}
                            for i,d in enumerate(rhythm.DAYS)],
                  p_null=p,p_adjusted=p_adj,bonferroni_m=m,lowest_day=rhythm.DAYS[int(mean.argmin())],
                  rest_index=float(mean[r]),rest_is_lowest=lowest,ci_upper_below_one=bool(hi[r]<1),
                  significant=bool(result["status"]=="ok" and lowest and hi[r]<1 and p_adj<config["alpha"]))
    return result


def analyse_family(counts, manifest, config=None, subset="all", control=False):
    validate_counts(counts)
    settings = {**rhythm.DEFAULTS,**(config or {})}
    frame = counts[counts.type.isin([1,2])] if control else counts[counts.type==0]
    if subset == "day":
        frame = frame[frame.daynight=="D"]
    return [analyse_stream(frame[(frame.country==country)&(frame.stream==stream)],country,stream,subset,
                           manifest,settings,control)
            for country in rhythm.REST_DAYS for stream in rhythm.STREAMS]


def run_counts(counts, manifest, output_dir, label="REAL FIRMS DATA", config=None):
    """Run the unchanged statistical gate on prepared multiplicities, in staging."""
    from .aggregate_archives import write_json
    source_label = str(counts.attrs.get("label",manifest.get("label","")))
    if any(word in source_label.upper() for word in ["SYNTHETIC","FAKE","MOCK"]):
        label = source_label
    settings = {**rhythm.DEFAULTS,**(config or {})}
    main = analyse_family(counts,manifest,settings)
    day = analyse_family(counts,manifest,settings,subset="day")
    controls = analyse_family(counts,manifest,settings,control=True)
    gate = rhythm.make_gate(main,controls,label)
    result = {"phase":"prepared-count statistics; statistical eligibility is not deployment approval",
              "integration_approved":False,"gate":gate,"controls":controls,
              "countries":{c:{"rest_day":rest,"streams":[r for r in main if r["country"]==c],
                               "daytime_streams":[r for r in day if r["country"]==c],
                               "status":gate["per_country"][c]["status"]} for c,rest in rhythm.REST_DAYS.items()},
              "diagnostics":{"representation":"Exact detection counts; n is multiplicity","rows_used":int(counts.n.sum()),
                             "settings":settings,"observation_coverage":"unknown","commissioning_guard":FIRST_COMPLETE_YEAR}}
    output = Path(output_dir)
    write_json(output/"rhythm_results.json",result)
    write_json(output/"kill_test_gate.json",gate)
    write_reports(result,output)
    return result


def write_reports(result, output_dir):
    """Format saved inference into complete reports; never rerun the statistics."""
    from .aggregate_archives import write_json
    output = Path(output_dir)
    output.mkdir(parents=True,exist_ok=True)
    main = [row for country in rhythm.REST_DAYS for row in result["countries"][country]["streams"]]
    day = [row for country in rhythm.REST_DAYS for row in result["countries"][country]["daytime_streams"]]
    flat = []
    label = result["gate"]["label"]
    for family,rows in [("vegetation_all",main),("vegetation_day",day),("static_control",result["controls"])]:
        for row in rows:
            entry = {k:v for k,v in row.items() if k not in {"weekdays","year_list","unverified_years","excluded_years"}}
            entry.update(label=label,family=family,year_list=",".join(map(str,row["year_list"])))
            for weekday in row["weekdays"]:
                entry.update({weekday["day"]:weekday["index"],weekday["day"]+"_lo":weekday["lo"],weekday["day"]+"_hi":weekday["hi"]})
            flat.append(entry)
    pd.DataFrame(flat).to_csv(output/"kill_test_results.csv",index=False)
    import matplotlib
    matplotlib.use("Agg")
    figure = rhythm._plot(main,output,label)
    diagnostics = {**result["diagnostics"],"label":label,"figure":figure,
                   "main_family_tests":len(rhythm.REST_DAYS)*len(rhythm.STREAMS),
                   "daytime_family":"separate exploratory sensitivity analysis; not used by gate",
                   "control_family":"separate diagnostic family; no dip is not proof of equivalence",
                   "report_note":"Formatted from saved exact-count inference; no statistical test was rerun."}
    write_json(output/"kill_test_diagnostics.json",diagnostics)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("preparations",nargs="+")
    parser.add_argument("--output",required=True)
    args = parser.parse_args()
    from .prepare_analysis import input_snapshot
    manifest,_ = input_snapshot(args.preparations)
    frames = [pd.read_parquet(Path(directory)/"rhythm_counts.parquet") for directory in args.preparations]
    result = run_counts(pd.concat(frames,ignore_index=True),manifest,args.output)
    print(json.dumps(result["gate"],indent=2))
