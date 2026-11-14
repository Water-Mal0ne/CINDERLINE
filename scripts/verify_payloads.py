"""Verify deployed JSON agrees with the pipeline's saved numerical outputs."""
import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

root = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--public-dir", type=Path, default=root / "web/public/data")
parser.add_argument("--processed-dir", type=Path, default=root / "data/processed")
parser.add_argument("--evaluation", type=Path, default=root / "reports/harmonization_eval.csv")
args = parser.parse_args()
public = args.public_dir
index = json.loads((public / "index.json").read_text(encoding="utf-8"))
saved_all = None
national_by_region = {}


def decode_table(payload):
    if "daily" in payload:
        return payload["daily"]
    assert payload.get("encoding") in {None, "column-dictionary-v1"}
    columns, dictionaries = payload["columns"], payload.get("dictionaries", {})
    assert len(set(columns)) == len(columns)
    assert not dictionaries or payload.get("encoding") == "column-dictionary-v1"
    assert set(dictionaries).issubset(columns)
    result = []
    for row in payload["rows"]:
        assert len(row) == len(columns)
        decoded = {}
        for name, value in zip(columns, row):
            if name in dictionaries:
                assert type(value) is int and 0 <= value < len(dictionaries[name])
                value = dictionaries[name][value]
            decoded[name] = value
        result.append(decoded)
    return result
evaluation = pd.read_csv(args.evaluation)
assert index["label"] == "REAL FIRMS DATA"
assert {entry["id"] for entry in index["regions"]} == set(evaluation.region)
checks = 0
for entry in index["regions"]:
    partition = args.processed_dir / f"harmonized_{entry['id']}.parquet"
    if partition.exists():
        saved = pd.read_parquet(partition)
    else:
        if saved_all is None:
            saved_all = pd.read_parquet(args.processed_dir / "harmonized.parquet")
        saved = saved_all[saved_all.region == entry["id"]]
    assert set(saved.region) == {entry["id"]}
    national_by_region[entry["id"]] = saved[saved.cell_id == "ALL"].copy()
    data = json.loads((public / entry["file"]).read_text(encoding="utf-8"))
    assert data["meta"]["label"] == index["label"]
    assert not ("daily" in data and "daily_compact" in data)
    national_rows = decode_table(data["daily_compact"]) if "daily_compact" in data else data["daily"]
    cell_rows = []
    for cell in data["cells"]:
        if "file" in cell:
            payload = json.loads((public / cell["file"]).read_text(encoding="utf-8"))
            rows = decode_table(payload)
        else:
            rows = cell["daily"]
        cell_rows.append((cell["id"], rows))
    for cell, rows in [("ALL", national_rows), *cell_rows]:
        expected = saved[(saved.region == entry["id"]) & (saved.cell_id == cell)].sort_values("date")
        actual = pd.DataFrame(rows).sort_values("date")
        assert len(actual) == len(expected), (entry["id"], cell)
        assert actual.date.tolist() == expected.date.astype(str).tolist()
        for col in ["raw_terra", "raw_aqua", "raw_viirs", "raw", "harmonized", "lo", "hi"]:
            np.testing.assert_allclose(pd.to_numeric(actual[col]), expected[col], atol=1e-5, equal_nan=True)
            checks += len(actual)
        for col in ["source", "coverage", "model"]:
            assert actual[col].tolist() == expected[col].tolist(), (entry["id"], cell, col)
    for row in data["eval"]:
        match = evaluation[(evaluation.region == entry["id"]) & (evaluation.model == row["model"])
                           & (evaluation.split == row["split"]) & (evaluation.aggregation == row["aggregation"])]
        assert len(match) == 1
        for field in ["mae", "bias_pct", "correlation", "peak_week_error"]:
            expected = match.iloc[0][field]
            actual = np.nan if row[field] is None else row[field]
            np.testing.assert_allclose(actual, expected, atol=1e-5, equal_nan=True)
            checks += 1
    gate = data.get("rhythm", {}).get("gate", {}).get("decision") if data.get("rhythm") else None
    assert gate in {"pass", "fail", "insufficient_data", None}
globe = json.loads((public / "globe.json").read_text(encoding="utf-8"))
assert {r["id"] for r in globe["coverage_regions"]} == {entry["id"] for entry in index["regions"]}
for entry in index["regions"]:
    region_cells = [cell for cell in globe["cells"] if cell["region"] == entry["id"]]
    national = national_by_region[entry["id"]]
    national["year"] = pd.to_datetime(national.date).dt.year
    totals = national.groupby("year").harmonized.sum(min_count=1)
    for i, year in enumerate(globe["years"]):
        if year in totals:
            values = [cell["values"][i] for cell in region_cells if cell["values"][i] is not None]
            np.testing.assert_allclose(sum(values), totals[year], atol=.1, rtol=1e-8)
            checks += 1
size = sum(p.stat().st_size for p in public.rglob("*") if p.is_file())
assert size < 50 * 1024 * 1024, f"Static data budget exceeded: {size}"
print(json.dumps({"regions": len(index["regions"]), "numeric_checks": checks,
                  "web_data_bytes": size, "status": "passed"}, indent=2))
