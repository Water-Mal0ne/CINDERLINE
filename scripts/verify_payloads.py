"""Verify deployed JSON agrees with the pipeline's saved numerical outputs."""
import json
from pathlib import Path

import numpy as np
import pandas as pd

root = Path(__file__).resolve().parents[1]
public = root / "web/public/data"
index = json.loads((public / "index.json").read_text(encoding="utf-8"))
saved = pd.read_parquet(root / "data/processed/harmonized.parquet")
evaluation = pd.read_csv(root / "reports/harmonization_eval.csv")
assert index["label"] == "REAL FIRMS DATA"
checks = 0
for entry in index["regions"]:
    data = json.loads((public / entry["file"]).read_text(encoding="utf-8"))
    assert data["meta"]["label"] == index["label"]
    cell_rows = []
    for cell in data["cells"]:
        if "file" in cell:
            payload = json.loads((public / cell["file"]).read_text(encoding="utf-8"))
            rows = payload.get("daily") or [dict(zip(payload["columns"], row)) for row in payload["rows"]]
        else:
            rows = cell["daily"]
        cell_rows.append((cell["id"], rows))
    for cell, rows in [("ALL", data["daily"]), *cell_rows]:
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
for entry in index["regions"]:
    region_cells = [cell for cell in globe["cells"] if cell["region"] == entry["id"]]
    national = saved[(saved.region == entry["id"]) & (saved.cell_id == "ALL")].copy()
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
