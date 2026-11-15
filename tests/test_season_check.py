"""Scientific invariants of the retrospective common-date sensitivity."""
import numpy as np
import pandas as pd
import pytest

from pipeline.review.season_check import outcomes, outage_masks


def test_exact_common_masks_and_boundary_padding():
    masks = outage_masks()
    assert len(masks["primary"]) == 73
    assert len(masks["padded"]) == 87
    assert set(masks["primary"]) < set(masks["padded"])
    assert pd.Timestamp("2024-06-01") in masks["primary"]
    assert pd.Timestamp("2024-11-04") in masks["primary"]
    assert pd.Timestamp("2020-08-15") not in masks["primary"]
    assert pd.Timestamp("2020-08-15") in masks["padded"]


def test_shared_mask_removes_outage_discrepancy_without_imputing_it():
    dates = pd.date_range("2020-01-01", "2020-12-31")
    reference = np.ones(len(dates))
    candidate = reference.copy()
    outage = dates.isin(outage_masks()["primary"])
    candidate[outage] = 0
    assert outcomes(reference, candidate, dates)["tv"] > 0
    result = outcomes(reference[~outage], candidate[~outage], dates[~outage])
    assert result["tv"] == 0
    assert result["reference_total"] == result["candidate_total"] == 348
    assert result["reference_total"] < 366


def test_positive_scaling_keeps_monthly_shape_on_both_masks():
    dates = pd.date_range("2024-01-01", "2024-12-31")
    reference = 2 + np.arange(len(dates)) % 29
    raw = 4 + np.arange(len(dates)) % 43
    for excluded in outage_masks().values():
        keep = ~dates.isin(excluded)
        original = outcomes(reference[keep], raw[keep], dates[keep])
        scaled = outcomes(reference[keep], raw[keep] * 0.17, dates[keep])
        assert scaled["tv"] == pytest.approx(original["tv"], abs=1e-12)
        assert scaled["annual_relative_error"] != pytest.approx(original["annual_relative_error"])


def test_no_month_support_is_undefined_but_recorded_zero_month_is_valid():
    dates = pd.date_range("2024-01-01", "2024-12-31")
    values = np.ones(len(dates))
    values[dates.month == 6] = 0
    recorded_zero = outcomes(values, values, dates)
    assert recorded_zero["tv"] == 0
    keep = dates.month != 6
    unsupported = outcomes(values[keep], values[keep], dates[keep])
    assert unsupported["tv"] is None
    assert unsupported["undefined_reason"] == "zero_retained_month:6"
    assert unsupported["peak_month_agrees"] is None
    assert unsupported["monthly_mae"] is None


def test_zero_total_is_not_perfect_agreement_and_invalid_inputs_fail():
    dates = pd.date_range("2021-01-01", "2021-12-31")
    zero, one = np.zeros(len(dates)), np.ones(len(dates))
    assert outcomes(zero, zero, dates)["undefined_reason"] == "zero_reference_total"
    assert outcomes(one, zero, dates)["undefined_reason"] == "zero_candidate_total"
    with pytest.raises(ValueError, match="paired daily support"):
        outcomes(one[:-1], one, dates)
    with pytest.raises(ValueError, match="Duplicate"):
        outcomes(one, one, dates[:-1].append(dates[-2:-1]))
    for invalid in (np.nan, np.inf, -1):
        bad = one.copy()
        bad[0] = invalid
        with pytest.raises(ValueError, match="Nonfinite|Negative"):
            outcomes(one, bad, dates)
