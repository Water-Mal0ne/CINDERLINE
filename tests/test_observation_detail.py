import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from pipeline.review.observation_detail import (
    CALENDAR_POLICY, COLUMNS, build, clean_observations, coordinate_index, export_month,
)


def observation(**changes):
    return {"latitude": 27.712345, "longitude": 85.312345, "acq_date": "2024-01-01",
            "acq_time": 104, "satellite": "N", "instrument": "VIIRS", "confidence": "n",
            "type": 0, "scan": .42, "track": .38, "frp": 0., "daynight": "N", **changes}


def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def test_filters_require_real_vegetation_quality_platform_and_valid_time():
    raw = pd.DataFrame([
        observation(), observation(confidence="high"), observation(confidence="l"),
        observation(type=1), observation(type=np.nan), observation(type=.5),
        observation(satellite="N20"), observation(acq_time=2360), observation(acq_time=100.5),
        observation(acq_date="2023-12-31"), observation(latitude=91), observation(longitude=np.inf),
    ])
    clean, stats = clean_observations(raw)
    assert len(clean) == 2
    assert clean.confidence.tolist() == ["n", "h"]
    assert stats["raw_rows"] == 12 and stats["retained_rows"] == 2


def test_positions_zero_frp_and_unknown_measurements_remain_distinguishable(tmp_path):
    clean, _ = clean_observations(pd.DataFrame([
        observation(), observation(latitude=27.712346, frp=np.nan, scan=-1, track=np.inf),
        observation(latitude=27.712347, frp=-2, daynight="unknown"),
    ]))
    descriptor = export_month(clean, "Nepal", "2024-01", tmp_path, "a" * 64)
    month = load(tmp_path / descriptor["file"].removeprefix("observations/"))
    rows = load(tmp_path / month["tiles"][0]["file"].removeprefix("observations/"))["rows"]
    assert rows[0][0:2] == [27.712345, 85.312345]
    assert rows[0][2] == "2024-01-01T01:04:00Z"
    assert rows[0][6] == 0
    assert rows[1][4:7] == [None, None, None]
    assert rows[2][6:] == [None, "?"]


def test_decimal_grid_boundaries_do_not_shift_negative_or_exact_coordinates():
    assert coordinate_index(29.9, .05) == 598
    assert coordinate_index(-29.9, .05) == -598
    assert coordinate_index(-29.900001, .05) == -599
    assert coordinate_index(0.049999, .05) == 0
    assert coordinate_index(0.05, .05) == 1
    assert coordinate_index(-0.000001, .05) == -1


def test_grid_and_spatial_tiles_preserve_all_records_including_repeated_passes(tmp_path):
    raw = pd.DataFrame([observation(latitude=a, longitude=b) for a, b in [
        (28.1, 84.1), (28.1, 84.1), (28.2, 85.7), (29.7, 84.2), (29.8, 85.8),
        (-29.9, -85.05), (90., 180.), (-90., -180.),
    ]])
    clean, _ = clean_observations(raw)
    descriptor = export_month(clean, "Nepal", "2024-01", tmp_path, "b" * 64, max_tile_rows=2)
    month = load(tmp_path / descriptor["file"].removeprefix("observations/"))
    assert month["count"] == sum(g[2] for g in month["grid"]) == sum(t["count"] for t in month["tiles"]) == 8
    assert [1799, 3599, 1] in month["grid"]
    assert [-1800, -3600, 1] in month["grid"]
    assert [-598, -1701, 1] in month["grid"]
    all_rows = []
    for tile in month["tiles"]:
        path = tmp_path / tile["file"].removeprefix("observations/")
        assert hashlib.sha256(path.read_bytes()).hexdigest() == tile["sha256"]
        payload = load(path)
        assert payload["columns"] == COLUMNS
        assert payload["count"] <= 2
        west, south, east, north = tile["bounds"]
        assert all(south <= r[0] <= north and west <= r[1] <= east for r in payload["rows"])
        all_rows.extend(payload["rows"])
    assert sum(r[0:2] == [28.1, 84.1] for r in all_rows) == 2
    assert len(all_rows) == 8
    assert any(t["bounds"][2] - t["bounds"][0] < 2 for t in month["tiles"])


def test_coincident_dense_records_are_listed_in_full_not_silently_sampled(tmp_path):
    clean, _ = clean_observations(pd.DataFrame([observation()] * 5))
    descriptor = export_month(clean, "Nepal", "2024-01", tmp_path, "c" * 64, max_tile_rows=2)
    month = load(tmp_path / descriptor["file"].removeprefix("observations/"))
    assert [t["count"] for t in month["tiles"]] == [2, 2, 1]
    assert len({t["id"] for t in month["tiles"]}) == 3
    assert month["grid"] == [[554, 1706, 5]]


def source_manifest(tmp_path, rows=None):
    path = tmp_path / "source.csv"
    pd.DataFrame(rows or [observation(), observation(acq_date="2024-07-10")]).to_csv(path, index=False)
    record = {"country": "Nepal", "sensor": "viirs-snpp", "year": 2024, "complete": True,
              "status": "complete", "path": str(path), "rows": len(rows or [1, 2]),
              "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
              "url": "https://firms.modaps.eosdis.nasa.gov/data/country/viirs-snpp/2024/viirs-snpp_2024_Nepal.csv"}
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps({"files": [record]}))
    return manifest, path, record


def test_build_retains_outage_date_records_and_explicitly_separates_calendar_policy(tmp_path):
    manifest, source, _ = source_manifest(tmp_path)
    index, receipt = build(manifest, tmp_path / "export", countries=["Nepal"], chunk_rows=1)
    country = index["countries"][0]
    assert len(country["months"]) == 12
    assert country["count"] == receipt["total_detections"] == 2
    assert country["months"][6]["count"] == 1  # Not removed by local-calendar outage masks.
    assert index["time_basis"] == "UTC" and index["calendar_policy"] == CALENDAR_POLICY
    assert "local civil dates" in index["calendar_policy"]
    assert "no fire" in index["coverage_note"]
    assert str(source) not in json.dumps(index)
    empty = load(tmp_path / "export/Nepal/2024-02.json")
    assert empty["count"] == 0 and empty["grid"] == [] and empty["tiles"] == []
    assert len(empty["zero_record_dates"]) == 29
    assert "missing_observation_days" not in empty


def test_source_hash_or_manifest_count_mismatch_fails(tmp_path):
    manifest, source, record = source_manifest(tmp_path)
    source.write_text(source.read_text() + "\n")
    with pytest.raises(ValueError, match="hash mismatch"):
        build(manifest, tmp_path / "export", countries=["Nepal"])
    record["sha256"] = hashlib.sha256(source.read_bytes()).hexdigest()
    record["rows"] += 1
    manifest.write_text(json.dumps({"files": [record]}))
    with pytest.raises(ValueError, match="row count mismatch"):
        build(manifest, tmp_path / "export2", countries=["Nepal"])


def test_unverified_or_duplicate_source_is_rejected(tmp_path):
    manifest, _, record = source_manifest(tmp_path)
    record["complete"] = False
    manifest.write_text(json.dumps({"files": [record]}))
    with pytest.raises(ValueError, match="not declared complete"):
        build(manifest, tmp_path / "export", countries=["Nepal"])
    manifest.write_text(json.dumps({"files": [record, record]}))
    with pytest.raises(ValueError, match="exactly one"):
        build(manifest, tmp_path / "export", countries=["Nepal"])
