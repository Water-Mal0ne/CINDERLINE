"""Cache provenance and portable compact-cell export regressions."""
from copy import deepcopy
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from pipeline.calendar import DAY_FIELDS, build, json_safe, normalized_daily
from pipeline.run_all import manifest_signature


def manifest_fixture():
    return {"files": [
        {"country": "Nepal", "sensor": "modis", "year": 2012, "sha256": "one",
         "complete": True, "status": "complete", "path": "C:/original/nepal.csv"},
        {"country": "Nepal", "sensor": "viirs-snpp", "year": 2013, "sha256": "two",
         "complete": True, "status": "complete", "path": "C:/original/viirs.csv"},
        {"country": "United_States", "sensor": "modis", "year": 2012, "sha256": "three",
         "complete": True, "status": "complete", "path": "C:/original/us.csv"},
    ]}


@pytest.mark.parametrize("field,value", [
    ("sha256", "changed-data"), ("complete", False), ("status", "failed"),
    ("year", 2011), ("sensor", "viirs-snpp"),
])
def test_manifest_signature_detects_changed_data_or_archive_eligibility(field, value):
    original = manifest_fixture()
    changed = deepcopy(original)
    changed["files"][0][field] = value
    assert manifest_signature(changed, ["Nepal"]) != manifest_signature(original, ["Nepal"])


def test_manifest_signature_ignores_paths_transfer_metadata_and_order():
    original = manifest_fixture()
    changed = deepcopy(original)
    changed["files"].reverse()
    for row in changed["files"]:
        row["path"] = "/different/workstation/archive.csv"
        row["downloaded_at"] = "2026-11-15T00:00:00Z"
    assert manifest_signature(changed, ["United_States", "Nepal"]) == manifest_signature(original, ["Nepal", "United_States"])


def test_manifest_signature_is_scoped_to_selected_countries():
    original = manifest_fixture()
    changed = deepcopy(original)
    changed["files"][2]["sha256"] = "new-us-data"
    assert manifest_signature(changed, ["Nepal"]) == manifest_signature(original, ["Nepal"])
    assert manifest_signature(changed, ["United_States"]) != manifest_signature(original, ["United_States"])
    assert manifest_signature(original, ["Nepal"]) != manifest_signature(original, ["Nepal", "United_States"])


def export_fixture():
    rows, coordinates = [], []
    for region, cell, lat, lon in [("Nepal", "27.00:85.00", 27.125, 85.125),
                                  ("United_States", "38.00:-122.00", 38.125, -121.875)]:
        coordinates.append(dict(country=region, cell_id=cell, lat=lat, lon=lon))
        for date, aqua, viirs, value, lower, upper, source in [
            ("2012-01-01", 12.0, np.nan, 12.0, np.nan, np.nan, "observed Aqua"),
            ("2013-01-01", 10.0, 40.0, 9.123456789, 8.0, 11.0, "converted VIIRS"),
        ]:
            for cell_id in ["ALL", cell]:
                rows.append(dict(date=date, region=region, cell_id=cell_id,
                                 raw_terra=7.0, raw_aqua=aqua, raw_viirs=viirs,
                                 raw=aqua if np.isnan(viirs) else viirs, harmonized=value,
                                 lo=lower, hi=upper, coverage="observation coverage unknown",
                                 source=source, model="Aqua reference" if source == "observed Aqua" else "M1"))
    return pd.DataFrame(rows), pd.DataFrame(coordinates)


def test_cell_exports_use_portable_filenames_and_compact_rows_round_trip(tmp_path):
    data, detections = export_fixture()
    regions = build(data, pd.DataFrame(), None, tmp_path, detections=detections,
                    label="SYNTHETIC DATA")
    assert len(regions) == 2
    all_files = []
    for region in regions:
        region_file = json.loads((tmp_path / region["file"]).read_text(encoding="utf-8"))
        assert region_file["meta"]["label"] == "SYNTHETIC DATA"
        assert len(region_file["cells"]) == 1
        for cell in region_file["cells"]:
            assert "daily" not in cell, "Cell detail should be loaded only when selected."
            relative = Path(cell["file"])
            assert not relative.is_absolute()
            assert ":" not in str(relative), "Colon paths create NTFS alternate data streams."
            assert ".." not in relative.parts
            actual_path = (tmp_path / relative).resolve()
            assert actual_path.is_relative_to(tmp_path.resolve())
            assert actual_path.is_file()
            all_files.append(actual_path)
            compact = json.loads(actual_path.read_text(encoding="utf-8"))
            assert compact["columns"] == DAY_FIELDS
            assert all(len(row) == len(DAY_FIELDS) for row in compact["rows"])
            decoded = [dict(zip(compact["columns"], row)) for row in compact["rows"]]
            expected = normalized_daily(data[(data.region == region["id"]) & (data.cell_id == cell["id"])])
            assert decoded == json_safe(expected.to_dict("records"))
            assert decoded[0]["raw_viirs"] is None
            assert decoded[0]["raw"] == 12
            assert decoded[1]["harmonized"] == 9.12346
    assert len(set(all_files)) == len(all_files)
