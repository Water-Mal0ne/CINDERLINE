"""2025 extension: labelled rows appended, frozen-model metadata, and the continuity check is reported for every country."""
import json
from pathlib import Path

import pandas as pd

from pipeline.streaming.estimate_dictionary import decode_table

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "web/public/data"
COUNTRIES = ["Australia", "Bangladesh", "Brazil", "Egypt", "India", "Nepal", "United_States"]
SOURCE = "converted VIIRS, beyond the validation period"


def frame(path):
    payload = json.loads(path.read_text(encoding="utf-8"))
    table = payload["daily_compact"] if "daily_compact" in payload else payload
    return payload, pd.DataFrame(decode_table(table), columns=table["columns"])


def test_2025_rows_are_labelled_and_complete():
    model = json.loads((ROOT / "reports/harmonization_model.json").read_text(encoding="utf-8"))
    for country in COUNTRIES:
        payload, df = frame(DATA / f"{country}.json")
        assert payload["meta"]["period_end"] == "2025-12-31"
        assert "beyond the validation period" in payload["meta"]["extension_note"]
        national = df[df.cell_id == "ALL"]
        y25 = national[national.date.str.startswith("2025")]
        assert len(y25) == 365
        assert len(national[national.date < "2025"]) == 8036, "2003-2024 rows unchanged in number"
        ok = y25[y25.source != "no observation"]
        assert (ok.source == SOURCE).all()
        assert ok.lo.isna().all() and ok.hi.isna().all(), "no calibration interval is claimed for 2025"
        assert (ok.model == model["selection"][country]["selected"]).all()
        assert ok.harmonized.notna().all() and (ok.harmonized >= 0).all()
        assert (y25.source == "no observation").sum() <= 1
        for cell in payload["cells"]:
            _, cdf = frame(DATA / cell["file"])
            assert (cdf.date.str.startswith("2025")).sum() == 365


def test_continuity_check_reported_for_every_country():
    cont = pd.read_csv(ROOT / "reports/review/extend2025/continuity_2025.csv")
    assert set(cont.country) == set(COUNTRIES)
    assert cont[["bias_pct_2025", "weekly_r_2025", "bias_pct_test_2020_2024", "weekly_r_test_2020_2024"]].notna().all().all()
