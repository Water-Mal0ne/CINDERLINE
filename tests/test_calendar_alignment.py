import copy

import pandas as pd
import pytest

from pipeline.review.calendar_alignment import (
    aligned_values, correction_values, encode_corrections, globe_view_hash,
)


def data():
    globe = {"years": [2022, 2024], "archive_manifest_fingerprint": "a" * 64,
             "cells": [{"id": "A:0:0", "region": "A", "values": [10., 20.]},
                       {"id": "A:1:1", "region": "A", "values": [None, 0.]}]}
    model = {"selection": {"A": {"selected": "M1"}}, "ratios": {"B1": .5, "M1": {"A|D:low": .25}}}
    return globe, model


def frame():
    return pd.DataFrame([
        ("A", "0:0", "2022-07-26", 2022, "VIIRS", "D:low", 0, 8),
        ("A", "0:0", "2022-07-26", 2022, "Aqua", "D:low", 0, 9),
        ("A", "0:0", "2022-07-26", 2022, "VIIRS", "D:low", 2, 7),
        ("A", "0:0", "2022-07-25", 2022, "VIIRS", "D:low", 0, 6),
        ("A", "0:0", "2024-01-01", 2024, "VIIRS", "unknown", 0, 4),
    ], columns=["country", "cell_id", "local_date", "year", "stream", "stratum", "type", "n"])


def test_mask_uses_local_dates_supplier_stream_and_vegetation_counts_only():
    _, model = data()
    counts, raw = correction_values(frame(), {"A": {"2022-07-26", "2024-01-01"}},
                                    {("A", 2022): "VIIRS", ("A", 2024): "VIIRS"}, model)
    assert raw == 12
    assert counts == {("A", "0:0", 2022, "VIIRS", "D:low"): 8,
                      ("A", "0:0", 2024, "VIIRS", "unknown"): 4}


def test_new_year_uses_local_year_not_archive_year_and_detects_inconsistent_input():
    f = frame().iloc[[4]].copy()
    f["file_year"] = 2023
    counts, raw = correction_values(f, {"A": {"2024-01-01"}}, {("A", 2024): "VIIRS"}, {})
    assert raw == 4 and next(iter(counts))[2] == 2024
    f["year"] = 2023
    with pytest.raises(ValueError, match="local date"):
        correction_values(f, {"A": {"2024-01-01"}}, {("A", 2024): "VIIRS"}, {})


def test_frozen_strata_and_fallback_are_applied_without_new_fitting():
    globe, model = data()
    original = copy.deepcopy(model)
    values, corrections = encode_corrections({("A", "0:0", 2022, "VIIRS", "D:low"): 8,
                                               ("A", "0:0", 2024, "VIIRS", "unknown"): 4}, globe, model)
    assert values == [2.]
    assert corrections == {"2022": [[0, 0]], "2024": [[0, 0]]}
    assert model == original


def test_aqua_source_removes_observed_count_without_viirs_ratio():
    globe, model = data()
    values, corrections = encode_corrections({("A", "0:0", 2022, "Aqua", "D:low"): 8}, globe, model)
    assert values == [8.] and corrections == {"2022": [[0, 0]]}


@pytest.mark.parametrize("counts", [
    {("A", "2:2", 2022, "VIIRS", "D:low"): 1},
    {("A", "0:0", 2025, "VIIRS", "D:low"): 1},
    {("A", "1:1", 2022, "VIIRS", "D:low"): 1},
    {("A", "0:0", 2022, "VIIRS", "D:low"): 100},
])
def test_wrong_cell_year_missing_source_or_excess_deduction_is_rejected(counts):
    globe, model = data()
    with pytest.raises(ValueError):
        encode_corrections(counts, globe, model)


def test_original_nulls_and_zero_survive_and_fully_masked_year_is_unavailable():
    globe, _ = data()
    original = copy.deepcopy(globe)
    overlay = {"deductions": [2.], "corrections": {"2022": [[0, 0]]},
               "coverage": {"2022": {"retained_dates": 349}, "2024": {"retained_dates": 0}}}
    assert aligned_values(globe, overlay) == [[8., None], [None, None]]
    assert globe == original
    overlay["coverage"]["2024"]["retained_dates"] = 366
    assert aligned_values(globe, overlay)[1] == [None, 0.]


def test_source_identity_binds_values_ids_years_and_archive_identity():
    globe, _ = data()
    original = globe_view_hash(globe)
    for mutate in [lambda g: g["cells"][0]["values"].__setitem__(0, 11.),
                   lambda g: g["cells"].reverse(), lambda g: g["years"].reverse(),
                   lambda g: g.__setitem__("archive_manifest_fingerprint", "b" * 64)]:
        changed = copy.deepcopy(globe)
        mutate(changed)
        assert globe_view_hash(changed) != original


@pytest.mark.parametrize("bad", [-1, 1.5, float("nan")])
def test_invalid_raw_multiplicity_is_rejected(bad):
    f = frame().iloc[[0]].copy()
    f["n"] = bad
    with pytest.raises(ValueError, match="multiplicities"):
        correction_values(f, {"A": {"2022-07-26"}}, {("A", 2022): "VIIRS"}, {})
