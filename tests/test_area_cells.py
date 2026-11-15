"""Area-of-interest cells: published files reconcile with the national series and respect size limits."""
import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
AREA = ROOT / "web/public/data/area"


def test_cells_sum_to_published_national_series():
    rec = pd.read_csv(ROOT / "reports/review/area/reconciliation.csv")
    assert set(rec.country) == {"Australia", "Bangladesh", "Brazil", "Egypt", "India", "Nepal", "United_States"}
    assert (rec.months_compared >= 250).all()
    # Only January 2013 (UTC-to-local spill from the 2012 VIIRS archive, absent locally) may exceed rounding.
    assert (rec.max_rel_diff < 0.01).all()
    assert (rec.total_rel_diff.abs() < 1e-4).all()
    assert (rec["months_rel_diff_over_0.1pct"] <= 1).all()
    flagged = rec[rec.max_rel_diff > 1e-3]
    assert set(flagged.worst_month) <= {"2013-01"}


def test_area_files_are_small_sparse_and_labelled():
    total = 0
    for path in sorted(AREA.glob("*.json")):
        size = path.stat().st_size
        total += size
        assert size < 25 * 2**20
        payload = json.loads(path.read_text(encoding="utf-8"))
        assert payload["note"] == "Area values use national calibration; local accuracy has not been validated."
        assert payload["months"] == 264 and payload["first_month"] == "2003-01"
        assert len(payload["lat"]) == len(payload["lon"]) == len(payload["series"])
        for series in payload["series"][:200]:
            assert len(series) % 2 == 0 and all(isinstance(v, int) for v in series)
            assert sum(series[0::2]) < 264
    assert total < 30 * 2**20
