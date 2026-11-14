"""Measure an exactly reversible JSON dictionary representation in a fresh stage."""
from pathlib import Path
import argparse
import json
import shutil
from .aggregate_archives import write_json


def encode(value):
    return json.dumps(value,separators=(",",":"),ensure_ascii=True,allow_nan=False)


def compact_table(columns, rows):
    encoded = [list(row) for row in rows]
    dictionaries = {}
    for index,column in enumerate(columns):
        originals = [row[index] for row in rows]
        unique, by_json, codes = [],{},[]
        for value in originals:
            key = encode(value)  # Distinguishes booleans, integers, floats, null and strings.
            if key not in by_json:
                by_json[key] = len(unique)
                unique.append(value)
            codes.append(by_json[key])
        overhead = len(encode({column:unique}).encode())+1
        if len(encode(codes).encode())+overhead < len(encode(originals).encode()):
            dictionaries[column] = unique
            for row,code in zip(encoded,codes):
                row[index] = code
    result = {"encoding":"column-dictionary-v1","columns":columns,"rows":encoded}
    if dictionaries:
        result["dictionaries"] = dictionaries
    # Exact serialized representation catches types and precision changes too.
    decoded = decode_table(result)
    if encode(decoded) != encode(rows):
        raise AssertionError("Dictionary encoding changed original JSON values")
    return result


def decode_table(table):
    columns = table["columns"]
    dictionaries = table.get("dictionaries",{})
    result = []
    for row in table["rows"]:
        if len(row) != len(columns):
            raise ValueError("Dictionary row width differs from columns")
        decoded = []
        for i,value in enumerate(row):
            if columns[i] in dictionaries:
                values = dictionaries[columns[i]]
                if isinstance(value,bool) or not isinstance(value,int) or not 0<=value<len(values):
                    raise ValueError("Invalid dictionary index")
                decoded.append(values[value])
            else:
                decoded.append(value)
        result.append(decoded)
    return result


def estimate(source, output):
    source,output = Path(source),Path(output)
    if output.exists():
        raise ValueError("Use a fresh output directory to preserve prior estimates")
    output.mkdir(parents=True)
    listing,checked = [],0
    for path in sorted(source.rglob("*")):
        if not path.is_file():
            continue
        relative = path.relative_to(source)
        target = output/relative
        target.parent.mkdir(parents=True,exist_ok=True)
        original_bytes = path.stat().st_size
        if path.suffix==".json" and path.parent.name=="cells":
            payload = json.loads(path.read_text())
            compact = compact_table(payload["columns"],payload["rows"])
            target.write_text(encode(compact),encoding="utf-8")
            checked += len(payload["rows"])
        elif path.suffix==".json" and path.stem not in ["index","globe","globe.metrics"]:
            payload = json.loads(path.read_text())
            if isinstance(payload.get("daily"),list) and payload["daily"]:
                daily = payload.pop("daily")
                columns = list(daily[0])
                rows = [[row[column] for column in columns] for row in daily]
                payload["daily_compact"] = compact_table(columns,rows)
                restored = [dict(zip(columns,row)) for row in decode_table(payload["daily_compact"])]
                if encode(restored)!=encode(daily):
                    raise AssertionError("National daily records changed")
                target.write_text(encode(payload),encoding="utf-8")
                checked += len(daily)
            else:
                shutil.copyfile(path,target)
        else:
            shutil.copyfile(path,target)
        listing.append({"file":str(relative),"original_bytes":original_bytes,"encoded_bytes":target.stat().st_size})
    baseline = json.loads((source.parent/"PAYLOAD_BUDGET.json").read_text())
    total = sum(r["encoded_bytes"] for r in listing)
    projected = total+baseline["shared_map_bytes"]+baseline["current_non_data_dist_bytes"]
    report = {"phase":"column-dictionary-v1 payload encoding",
              "rows_roundtrip_checked":checked,"all_json_values_exact":True,
              "original_data_bytes":sum(r["original_bytes"] for r in listing),"encoded_data_bytes":total,
              "projected_static_bytes":projected,"initial_budget_bytes":50*1024**2,"within_initial_budget":projected<=50*1024**2,
              "largest_files":sorted(listing,key=lambda r:r["encoded_bytes"],reverse=True)[:12],
              "individual_files_within_25MiB":all(r["encoded_bytes"]<=25*1024**2 for r in listing),
              "globe_unchanged":True,"csv_exports_unchanged":True,
              "decoder_contract":"For each table column present in dictionaries, a row entry is a nonnegative integer index into that column's dictionary; other entries remain original JSON values. National daily_compact normalizes back to daily records before use."}
    write_json(output.parent/"DICTIONARY_BUDGET.json",report)
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source")
    parser.add_argument("output")
    args = parser.parse_args()
    print(json.dumps(estimate(args.source,args.output),indent=2))
