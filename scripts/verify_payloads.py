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
    for cell, rows in [("ALL", data["daily"]), *[(c["id"], c["daily"]) for c in data["cells"]]]:
        expected = saved[(saved.region == entry["id"]) & (saved.cell_id == cell)].sort_values("date")
        actual = pd.DataFrame(rows).sort_values("date")
        assert len(actual) == len(expected), (entry["id"], cell)
        assert actual.date.tolist() == expected.date.astype(str).tolist()
        for col in ["raw_terra", "raw_aqua", "raw_viirs", "harmonized", "lo", "hi"]:
            np.testing.assert_allclose(pd.to_numeric(actual[col]), expected[col], atol=1e-5, equal_nan=True)
            checks += len(actual)
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
size = sum(p.stat().st_size for p in public.glob("*"))
assert size < 50 * 1024 * 1024, f"Static data budget exceeded: {size}"
print(json.dumps({"regions": len(index["regions"]), "numeric_checks": checks,
                  "web_data_bytes": size, "status": "passed"}, indent=2))
